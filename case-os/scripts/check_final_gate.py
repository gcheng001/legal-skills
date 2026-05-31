#!/usr/bin/env python3
"""
FINAL 门禁脚本
在生成诉讼文书前，校验 S10 blocking_result
只有 is_blocked=false 且 can_enter_final=true 时才允许放行
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

S10_SCHEMA_PATH = Path(__file__).parent.parent.parent / "case-s10-hallucination" / "schema" / "s10_output_schema.json"

# S10 文件路径优先级（原告视角）
S10_PATHS = [
    "intermediate/原告九步法/S10-幻觉校验和八个一致报告.md",
    "intermediate/原告九步法/S10-幻觉校验和八个一致.md",
    "S10-幻觉校验和八个一致报告.md",
]

# S10 文件路径优先级（被告视角）
S10_PATHS_DEFENDANT = [
    "intermediate/被告九步法/S10-幻觉校验和八个一致报告.md",
    "intermediate/被告九步法/S10-幻觉校验和八个一致.md",
    "S10-幻觉校验和八个一致报告-被告.md",
]


def find_s10_path(project_path: str, role: str = "plaintiff") -> Optional[str]:
    """查找 S10 输出文件路径"""
    base = Path(project_path)
    paths = S10_PATHS if role == "plaintiff" else S10_PATHS_DEFENDANT
    for p in paths:
        if (base / p).exists():
            return str(base / p)
        # 也尝试相对于 intermediate
        intermediate = base / "intermediate"
        if role == "plaintiff":
            candidate = intermediate / "原告九步法" / Path(p).name
        else:
            candidate = intermediate / "被告九步法" / Path(p).name
        if candidate.exists():
            return str(candidate)
    return None


def parse_frontmatter(content: str) -> Optional[dict]:
    """解析 JSON frontmatter"""
    pattern = r'^---\n(.*?)\n---\n'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None


def load_s10_json(project_path: str, role: str = "plaintiff") -> Tuple[Optional[dict], str]:
    """
    加载 S10 JSON frontmatter
    Returns: (json_data, error_message)
    """
    s10_path = find_s10_path(project_path, role)
    if not s10_path:
        return None, f"S10文件未找到（角色：{role}）"

    try:
        with open(s10_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None, f"读取S10文件失败: {e}"

    fm = parse_frontmatter(content)
    if not fm:
        return None, f"S10文件无法解析JSON frontmatter: {s10_path}"

    return fm, ""


def validate_s10_schema(s10_data: dict) -> Tuple[bool, str]:
    """
    使用 S10 strict schema 校验
    Returns: (is_valid, error_message)
    """
    try:
        import jsonschema
        with open(S10_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        jsonschema.validate(s10_data, schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, f"S10 schema校验失败: {e.message}"
    except Exception as e:
        return False, f"S10 schema校验异常: {e}"


def check_blocking_result(s10_data: dict) -> Tuple[bool, str]:
    """
    校验 blocking_result
    Returns: (passes_gate, message)
    """
    br = s10_data.get("blocking_result", {})
    if not br:
        return False, "blocking_result 字段缺失"

    is_blocked = br.get("is_blocked")
    can_enter_final = br.get("can_enter_final")

    if is_blocked is None or can_enter_final is None:
        return False, f"blocking_result 关键字段缺失: is_blocked={is_blocked}, can_enter_final={can_enter_final}"

    if is_blocked is True:
        reasons = br.get("blocking_reasons", [])
        ec_failures = br.get("ec_critical_failures", [])
        msg = f"门禁阻断: is_blocked=true"
        if reasons:
            msg += f", 原因: {', '.join(reasons)}"
        if ec_failures:
            msg += f", EC失败: {', '.join(ec_failures)}"
        return False, msg

    if can_enter_final is not True:
        return False, f"门禁阻断: can_enter_final={can_enter_final} (应为true)"

    return True, "门禁通过"


def check_final_gate(project_path: str, role: str = "plaintiff", verbose: bool = False) -> Tuple[int, str]:
    """
    执行 FINAL 门禁检查

    Args:
        project_path: 案件项目路径
        role: 待生成文书的角色；门禁统一读取案件级原告链 S10 输出
        verbose: 是否输出详细信息

    Returns:
        (exit_code, message)
        exit_code: 0=通过, 1=阻断
    """
    # 1. 加载 S10 JSON
    # S10 是案件级 FINAL 门禁输出，两类正式文书均读取原告主链结果。
    s10_data, err = load_s10_json(project_path, "plaintiff")
    if not s10_data:
        return 1, f"[阻断] {err}"

    if verbose:
        print(f"[*] 已加载 S10 文件")

    # 2. Schema 校验
    valid, err = validate_s10_schema(s10_data)
    if not valid:
        return 1, f"[阻断] S10 schema校验失败: {err}"

    if verbose:
        print(f"[*] S10 schema校验通过")

    # 3. blocking_result 校验
    passed, msg = check_blocking_result(s10_data)
    if not passed:
        return 1, f"[阻断] {msg}"

    if verbose:
        print(f"[*] {msg}")

    return 0, msg


def main():
    import argparse
    parser = argparse.ArgumentParser(description='FINAL 门禁检查')
    parser.add_argument('--project', required=True, help='项目路径')
    parser.add_argument('--role', default='plaintiff', choices=['plaintiff', 'defendant'],
                        help='待生成文书角色（门禁统一读取原告主链 S10）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细信息')
    args = parser.parse_args()

    exit_code, msg = check_final_gate(args.project, args.role, args.verbose)
    print(msg)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
