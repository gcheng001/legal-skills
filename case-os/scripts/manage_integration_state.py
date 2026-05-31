#!/usr/bin/env python3
"""Manage the local structured state contract for case-os.

This module writes only two derived files under a case directory:
`_archive/case-os-state.json` and `_archive/feishu-publish.json`.
It performs no network operation and does not alter source materials.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
STATE_SCHEMA_PATH = ROOT_DIR / "schema" / "case_os_state_schema.json"
PUBLISH_SCHEMA_PATH = ROOT_DIR / "schema" / "feishu_publish_schema.json"
STATE_NAME = "case-os-state.json"
PUBLISH_NAME = "feishu-publish.json"
CONFIRMATION_REQUIRED_A = {"A4", "A5"}
CONFIRMATION_REQUIRED_B = {"S1", "S5", "S6", "S8", "S9"}
S10_FILES = (
    "intermediate/原告九步法/S10-幻觉校验和八个一致报告.md",
    "intermediate/原告九步法/S10-幻觉校验和八个一致.md",
    "S10-幻觉校验和八个一致报告.md",
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def schema_validator(path: Path) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        load_json(path),
        format_checker=jsonschema.FormatChecker(),
    )


def validate_document(data: dict[str, Any], schema_path: Path) -> None:
    schema_validator(schema_path).validate(data)


def archive_dir(case_path: Path) -> Path:
    archive = case_path / "_archive"
    archive.mkdir(parents=True, exist_ok=True)
    return archive


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def blank_step() -> dict[str, Any]:
    return {"status": "pending", "confirmed": False}


def blank_state(case_path: Path, migration_mode: str = "new") -> dict[str, Any]:
    return {
        "schema_version": "case-os-state-v1",
        "case_id": str(uuid.uuid4()),
        "generated_at": now_iso(),
        "validation_status": "valid",
        "case": {
            "folder_name": case_path.name,
            "case_name": None,
            "case_number": None,
            "cause": None,
            "parties": [],
            "confirmed_at": None,
        },
        "workflow": {
            "current_phase": "A",
            "current_step": "A1",
            "phase_a": {step: blank_step() for step in ("A1", "A2", "A3", "A4", "A5", "A6")},
            "phase_b": {},
            "final_gate": {"is_blocked": None, "can_enter_final": None, "source": None},
        },
        "confirmations": [],
        "deadlines": [],
        "pending_items": [],
        "blockers": [],
        "artifacts": [],
        "migration": {"mode": migration_mode, "source_conflicts": []},
    }


def load_or_initialize(case_path: Path, migration_mode: str = "new") -> dict[str, Any]:
    state_path = archive_dir(case_path) / STATE_NAME
    if state_path.exists():
        state = load_json(state_path)
        validate_document(state, STATE_SCHEMA_PATH)
        return state
    return blank_state(case_path, migration_mode)


def state_step_status(state: dict[str, Any]) -> str | None:
    workflow = state["workflow"]
    step = workflow["current_step"]
    if step in workflow["phase_a"]:
        return workflow["phase_a"][step]["status"]
    if isinstance(step, str) and step.startswith("S"):
        for name, entry in workflow["phase_b"].items():
            if f"/{step}" in name or name.endswith(step):
                return entry["status"]
    return None


def publish_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    if state["validation_status"] == "validation_required":
        return {
            "schema_version": "feishu-publish-v1",
            "case_id": state["case_id"],
            "case_name": state["case"]["folder_name"],
            "publish_status": "validation_required",
            "current_phase": None,
            "current_step": None,
            "step_status": None,
            "pending_confirmation_types": ["历史状态待人工校验"],
            "blocker_types": [],
            "deadlines": [],
            "updated_at": state["generated_at"],
        }

    deadlines = [
        {key: deadline[key] for key in ("task_id", "type", "due_date", "status")}
        for deadline in state["deadlines"]
        if deadline["confirmed"]
    ]
    return {
        "schema_version": "feishu-publish-v1",
        "case_id": state["case_id"],
        "case_name": state["case"]["folder_name"],
        "publish_status": "publishable",
        "current_phase": state["workflow"]["current_phase"],
        "current_step": state["workflow"]["current_step"],
        "step_status": state_step_status(state),
        "pending_confirmation_types": sorted({item["type"] for item in state["pending_items"]}),
        "blocker_types": sorted({item["type"] for item in state["blockers"]}),
        "deadlines": deadlines,
        "updated_at": state["generated_at"],
    }


def write_outputs(case_path: Path, state: dict[str, Any]) -> None:
    state["generated_at"] = now_iso()
    publish = publish_snapshot(state)
    validate_document(state, STATE_SCHEMA_PATH)
    validate_document(publish, PUBLISH_SCHEMA_PATH)
    archive = archive_dir(case_path)
    atomic_write(archive / STATE_NAME, state)
    atomic_write(archive / PUBLISH_NAME, publish)


def mark_pending_item(state: dict[str, Any], item_type: str, step: str) -> None:
    if not any(item["type"] == item_type for item in state["pending_items"]):
        state["pending_items"].append({"type": item_type, "step": step})


def clear_pending_for_step(state: dict[str, Any], step: str) -> None:
    state["pending_items"] = [item for item in state["pending_items"] if item.get("step") != step]


def resolve_confirmed_migration_conflicts(state: dict[str, Any]) -> None:
    conflicts = state.get("migration", {}).get("source_conflicts", [])
    if not conflicts:
        return
    confirmed_steps = {item["step"] for item in state["confirmations"]}
    covered = {
        f"{step} 历史状态为 completed 但无新契约明确确认记录"
        for step in confirmed_steps
    }
    remaining = [conflict for conflict in conflicts if conflict not in covered]
    if remaining == conflicts:
        return
    state["migration"]["source_conflicts"] = remaining
    if not remaining:
        state["validation_status"] = "valid"


def complete_internal_a6_if_ready(state: dict[str, Any]) -> None:
    phase_a = state["workflow"]["phase_a"]
    if all(phase_a[step]["confirmed"] for step in CONFIRMATION_REQUIRED_A):
        phase_a["A6"] = {"status": "completed", "confirmed": True}
        clear_pending_for_step(state, "A6")


def normalize_status(status: Any) -> str:
    mappings = {
        "review_pending": "pending_review",
        "shared_with_原告九步法": "shared",
    }
    value = mappings.get(status, status)
    if value in {"pending", "in_progress", "pending_review", "completed", "blocked", "shared"}:
        return value
    return "pending"


def sync_phase_b_index(case_path: Path, state: dict[str, Any]) -> None:
    index_path = case_path / "intermediate" / "_index.json"
    if not index_path.exists():
        return
    index = load_json(index_path)
    for side in ("原告九步法", "被告九步法"):
        entries = index.get(side, {})
        if not isinstance(entries, dict):
            continue
        for name, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            status = normalize_status(entry.get("status"))
            step_id = name.split("-", 1)[0]
            confirmed = any(item["step"] == step_id for item in state["confirmations"])
            state["workflow"]["phase_b"][f"{side}/{name}"] = {"status": status, "confirmed": confirmed}


def read_frontmatter(path: Path) -> dict[str, Any] | None:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        return None
    try:
        result = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return result if isinstance(result, dict) else None


def sync_final_gate(case_path: Path, state: dict[str, Any]) -> None:
    for relative in S10_FILES:
        candidate = case_path / relative
        if not candidate.exists():
            continue
        frontmatter = read_frontmatter(candidate)
        if not frontmatter:
            return
        blocking = frontmatter.get("blocking_result")
        if not isinstance(blocking, dict):
            return
        is_blocked = blocking.get("is_blocked")
        can_enter_final = blocking.get("can_enter_final")
        if isinstance(is_blocked, bool) and isinstance(can_enter_final, bool):
            state["workflow"]["final_gate"] = {
                "is_blocked": is_blocked,
                "can_enter_final": can_enter_final,
                "source": relative,
            }
        return


def refresh_state(case_path: Path, step: str | None) -> None:
    state = load_or_initialize(case_path)
    resolve_confirmed_migration_conflicts(state)
    complete_internal_a6_if_ready(state)
    sync_phase_b_index(case_path, state)
    sync_final_gate(case_path, state)
    if step and step != "unknown":
        if step in state["workflow"]["phase_a"]:
            state["workflow"]["current_phase"] = "A"
            state["workflow"]["current_step"] = step
            phase_a = state["workflow"]["phase_a"]
            if step in CONFIRMATION_REQUIRED_A:
                if not phase_a[step]["confirmed"]:
                    phase_a[step]["status"] = "pending_review"
                    mark_pending_item(state, f"{step}_律师确认", step)
            elif step == "A6":
                if all(phase_a[required]["confirmed"] for required in CONFIRMATION_REQUIRED_A):
                    phase_a[step] = {"status": "completed", "confirmed": True}
                else:
                    phase_a[step] = {"status": "pending_review", "confirmed": False}
                    mark_pending_item(state, "A6_前置确认不足", step)
            else:
                phase_a[step] = {"status": "completed", "confirmed": True}
        elif step.startswith("S"):
            state["workflow"]["current_phase"] = "B"
            state["workflow"]["current_step"] = step
            if step in CONFIRMATION_REQUIRED_B:
                mark_pending_item(state, f"{step}_律师确认", step)
    write_outputs(case_path, state)


def init_state(case_path: Path) -> None:
    state = load_or_initialize(case_path)
    write_outputs(case_path, state)


def validate_case(case_path: Path) -> None:
    archive = case_path / "_archive"
    state = load_json(archive / STATE_NAME)
    publish = load_json(archive / PUBLISH_NAME)
    validate_document(state, STATE_SCHEMA_PATH)
    validate_document(publish, PUBLISH_SCHEMA_PATH)


def confirmation_input(path: Path, expected_step: str) -> dict[str, Any]:
    data = load_json(path)
    allowed = {"step", "confirmed", "confirmed_at", "source", "case", "deadlines"}
    unexpected = set(data) - allowed
    if unexpected:
        raise ValueError(f"Confirmation contains unsupported fields: {sorted(unexpected)}")
    if data.get("step") != expected_step or data.get("confirmed") is not True:
        raise ValueError("Confirmation must explicitly confirm the requested step")
    if not isinstance(data.get("confirmed_at"), str) or not isinstance(data.get("source"), str):
        raise ValueError("Confirmation requires confirmed_at and source")
    return data


def confirm_state(case_path: Path, step: str, confirmation_file: Path) -> None:
    state = load_or_initialize(case_path)
    confirmation = confirmation_input(confirmation_file, step)
    record = {
        "step": step,
        "confirmed_at": confirmation["confirmed_at"],
        "source": confirmation["source"],
    }
    state["confirmations"] = [item for item in state["confirmations"] if item["step"] != step]
    state["confirmations"].append(record)
    clear_pending_for_step(state, step)
    if step in state["workflow"]["phase_a"]:
        state["workflow"]["phase_a"][step] = {"status": "completed", "confirmed": True}
    case_update = confirmation.get("case")
    if case_update is not None:
        if step != "A4" or not isinstance(case_update, dict):
            raise ValueError("Only an A4 confirmation may update local case management data")
        allowed_case = {"case_name", "case_number", "cause", "parties"}
        if set(case_update) - allowed_case:
            raise ValueError("Unsupported local case data in confirmation")
        state["case"].update(case_update)
        state["case"]["confirmed_at"] = confirmation["confirmed_at"]
    deadline_updates = confirmation.get("deadlines", [])
    if deadline_updates:
        normalized = []
        for deadline in deadline_updates:
            if not isinstance(deadline, dict):
                raise ValueError("Deadline must be an object")
            if set(deadline) - {"task_id", "type", "due_date", "status"}:
                raise ValueError("Unsupported deadline data")
            normalized.append(
                {
                    "task_id": deadline.get("task_id", str(uuid.uuid4())),
                    "type": deadline["type"],
                    "due_date": deadline["due_date"],
                    "status": deadline.get("status", "open"),
                    "confirmed": True,
                }
            )
        state["deadlines"] = normalized
    resolve_confirmed_migration_conflicts(state)
    complete_internal_a6_if_ready(state)
    write_outputs(case_path, state)


def scan_existing(case_path: Path) -> None:
    state = load_or_initialize(case_path, migration_mode="existing")
    state["migration"]["mode"] = "existing"
    conflicts: list[str] = []
    legacy_path = case_path / "_archive" / "phase-a-status.json"
    if legacy_path.exists():
        legacy = load_json(legacy_path)
        steps = legacy.get("steps", {})
        if isinstance(steps, dict):
            for step in ("A1", "A2", "A3"):
                entry = steps.get(step)
                if isinstance(entry, dict) and entry.get("status") == "completed":
                    state["workflow"]["phase_a"][step] = {"status": "completed", "confirmed": True}
            for step in CONFIRMATION_REQUIRED_A:
                entry = steps.get(step)
                if isinstance(entry, dict) and entry.get("status") == "completed":
                    conflicts.append(f"{step} 历史状态为 completed 但无新契约明确确认记录")
        if any(step not in {"A1", "A2", "A3", "A4", "A5", "A6"} for step in steps):
            conflicts.append("历史 Phase A 含旧编号步骤，需按 A1-A6 口径核认")
    sync_phase_b_index(case_path, state)
    sync_final_gate(case_path, state)
    state["migration"]["source_conflicts"] = conflicts
    if conflicts:
        state["validation_status"] = "validation_required"
        state["workflow"]["current_phase"] = None
        state["workflow"]["current_step"] = None
        state["deadlines"] = []
    else:
        state["validation_status"] = "valid"
    write_outputs(case_path, state)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage local case-os integration state")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "scan-existing", "validate"):
        cmd = subparsers.add_parser(command)
        cmd.add_argument("case_path")
    refresh = subparsers.add_parser("refresh")
    refresh.add_argument("case_path")
    refresh.add_argument("--step")
    confirm = subparsers.add_parser("confirm")
    confirm.add_argument("case_path")
    confirm.add_argument("--step", required=True)
    confirm.add_argument("--confirmation-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case_path = Path(args.case_path).expanduser().resolve()
    if not case_path.is_dir():
        raise ValueError(f"Case directory does not exist: {case_path}")
    if args.command == "init":
        init_state(case_path)
    elif args.command == "refresh":
        refresh_state(case_path, args.step)
    elif args.command == "confirm":
        confirm_state(case_path, args.step, Path(args.confirmation_file).expanduser().resolve())
    elif args.command == "scan-existing":
        scan_existing(case_path)
    elif args.command == "validate":
        validate_case(case_path)
    print(f"{args.command}: ok")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
