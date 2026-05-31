import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "manage_integration_state.py"
HOOK = ROOT / "scripts" / "case-post-step.sh"
STATE_SCHEMA = json.loads((ROOT / "schema" / "case_os_state_schema.json").read_text(encoding="utf-8"))
PUBLISH_SCHEMA = json.loads((ROOT / "schema" / "feishu_publish_schema.json").read_text(encoding="utf-8"))
SKILLS_ROOT = ROOT.parent


class IntegrationStateTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="case-os-integration-"))
        self.case_dir = self.tmpdir / "测试案件"
        self.case_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def run_cli(self, *args):
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def state(self):
        return json.loads((self.case_dir / "_archive" / "case-os-state.json").read_text(encoding="utf-8"))

    def publish(self):
        return json.loads((self.case_dir / "_archive" / "feishu-publish.json").read_text(encoding="utf-8"))

    def test_publish_snapshot_rejects_sensitive_or_unknown_fields(self):
        self.run_cli("init", str(self.case_dir))
        snapshot = self.publish()
        jsonschema.validate(snapshot, PUBLISH_SCHEMA)
        for forbidden in ("amount", "evidence"):
            unsafe = dict(snapshot)
            unsafe[forbidden] = "不得发布"
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(unsafe, PUBLISH_SCHEMA)

    def test_case_id_is_stable_across_refreshes(self):
        self.run_cli("init", str(self.case_dir))
        first_id = self.state()["case_id"]
        self.run_cli("refresh", str(self.case_dir), "--step", "A1")
        self.run_cli("refresh", str(self.case_dir), "--step", "A2")
        self.assertEqual(first_id, self.state()["case_id"])

    def test_a4_and_a5_do_not_complete_without_explicit_confirmation(self):
        self.run_cli("init", str(self.case_dir))
        self.run_cli("refresh", str(self.case_dir), "--step", "A4")
        self.run_cli("refresh", str(self.case_dir), "--step", "A5")
        phase_a = self.state()["workflow"]["phase_a"]
        for step in ("A4", "A5"):
            self.assertEqual("pending_review", phase_a[step]["status"])
            self.assertFalse(phase_a[step]["confirmed"])

    def test_confirm_requires_explicit_record_before_publishing_deadline(self):
        self.run_cli("init", str(self.case_dir))
        confirmation = self.case_dir / "a4-confirmation.json"
        confirmation.write_text(
            json.dumps(
                {
                    "step": "A4",
                    "confirmed": True,
                    "confirmed_at": "2026-05-25T20:00:00+08:00",
                    "source": "LOG.md#A4确认",
                    "case": {"case_name": "本地显示名称", "case_number": "不外发"},
                    "deadlines": [{"type": "举证期限", "due_date": "2026-06-01"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.run_cli("confirm", str(self.case_dir), "--step", "A4", "--confirmation-file", str(confirmation))
        self.assertEqual({"status": "completed", "confirmed": True}, self.state()["workflow"]["phase_a"]["A4"])
        self.assertEqual(1, len(self.publish()["deadlines"]))
        self.assertNotIn("case_number", self.publish())

    def test_existing_case_conflict_emits_validation_placeholder_without_deadlines(self):
        archive = self.case_dir / "_archive"
        archive.mkdir()
        (archive / "phase-a-status.json").write_text(
            json.dumps(
                {
                    "schema": "phase-a-v10.0",
                    "steps": {"A4": {"status": "completed"}, "A5": {"status": "completed"}},
                    "current_step": "A6",
                    "deadlines": [{"type": "举证期限", "due_date": "2026-06-01"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.run_cli("scan-existing", str(self.case_dir))
        state = self.state()
        snapshot = self.publish()
        self.assertEqual("validation_required", state["validation_status"])
        self.assertEqual("validation_required", snapshot["publish_status"])
        self.assertEqual(["历史状态待人工校验"], snapshot["pending_confirmation_types"])
        self.assertEqual([], snapshot["deadlines"])

    def test_a5_confirmation_auto_completes_internal_a6_and_resolves_migration_conflicts(self):
        archive = self.case_dir / "_archive"
        archive.mkdir()
        (archive / "phase-a-status.json").write_text(
            json.dumps(
                {
                    "schema": "phase-a-v10.0",
                    "steps": {"A4": {"status": "completed"}, "A5": {"status": "completed"}},
                    "current_step": "A6",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.run_cli("scan-existing", str(self.case_dir))

        for step in ("A4", "A5"):
            confirmation = self.case_dir / f"{step.lower()}-confirmation.json"
            confirmation.write_text(
                json.dumps(
                    {
                        "step": step,
                        "confirmed": True,
                        "confirmed_at": "2026-05-26T09:20:00+08:00",
                        "source": f"LOG.md#{step}确认",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.run_cli("confirm", str(self.case_dir), "--step", step, "--confirmation-file", str(confirmation))

        state = self.state()
        self.assertEqual("valid", state["validation_status"])
        self.assertEqual([], state["migration"]["source_conflicts"])
        self.assertEqual({"status": "completed", "confirmed": True}, state["workflow"]["phase_a"]["A6"])
        self.assertEqual("publishable", self.publish()["publish_status"])

    def test_s10_blocking_result_is_preserved_without_reinterpretation(self):
        s10 = self.case_dir / "intermediate" / "原告九步法" / "S10-幻觉校验和八个一致报告.md"
        s10.parent.mkdir(parents=True)
        self.run_cli("init", str(self.case_dir))
        for gate in (
            {"is_blocked": True, "can_enter_final": False},
            {"is_blocked": False, "can_enter_final": True},
        ):
            s10.write_text(
                "---\n" + json.dumps({"blocking_result": gate}, ensure_ascii=False) + "\n---\n# S10\n",
                encoding="utf-8",
            )
            self.run_cli("refresh", str(self.case_dir), "--step", "S10")
            self.assertEqual(gate, {
                "is_blocked": self.state()["workflow"]["final_gate"]["is_blocked"],
                "can_enter_final": self.state()["workflow"]["final_gate"]["can_enter_final"],
            })

    def test_hook_generates_only_local_state_outputs(self):
        subprocess.run(["bash", str(HOOK), str(self.case_dir), "A4"], check=True, capture_output=True, text=True)
        self.assertTrue((self.case_dir / "_archive" / "case-os-state.json").exists())
        self.assertTrue((self.case_dir / "_archive" / "feishu-publish.json").exists())
        self.assertFalse((self.case_dir / "案件仪表盘.html").exists())
        self.assertFalse((self.case_dir / "案件确认表.html").exists())
        hook_text = HOOK.read_text(encoding="utf-8")
        for forbidden in ("refresh_dashboard.py", "generate_confirm_data.py", "sync_feishu_deadline.py", "phase-a-status.json"):
            self.assertNotIn(forbidden, hook_text)

    def test_active_entrypoints_use_structured_state_contract(self):
        git_init = (SKILLS_ROOT / "case-git-init" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("manage_integration_state.py init", git_init)
        self.assertNotIn("echo '{\"schema\":\"phase-a", git_init)

        scan = (SKILLS_ROOT / "case-scan" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("case-os-state.json", scan)

        s1 = (SKILLS_ROOT / "case-s1-fixed-claim" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("A5（证据卡片与关系复核）复核完成且 A6 本地状态校验通过", s1)
        a5 = (SKILLS_ROOT / "case-evidence-cards" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("下一步：执行 A6", a5)
        self.assertIn("A6 内部门禁", a5)
        for skill in (
            "case-s1-fixed-claim",
            "case-s5-case-search",
            "case-s6-dispute-matrix",
            "case-s8-fact-finding",
            "case-s9-judgment-predict",
        ):
            text = (SKILLS_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn('仪表盘显"待律师确认"', text)
            self.assertIn("pending_review", text)


if __name__ == "__main__":
    unittest.main()
