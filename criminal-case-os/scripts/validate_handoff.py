#!/usr/bin/env python3
"""
刑事OS 交接包（Handoff Package）校验脚本
================================================
用法：
  python3 validate_handoff.py <handoff_file>

支持输入：
  - .json 文件
  - .yaml/.yml 文件（需 PyYAML）
  - .md 文件（自动提取 ```yaml ... ``` 代码块）

退出码：
  0 = 校验通过
  1 = 校验失败（不符合 schema）
  2 = 环境错误（缺库/文件不存在/用法错误）
"""
import sys
import os
import json
import re
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("错误：缺少 jsonschema 库。安装：python3 -m pip install jsonschema", file=sys.stderr)
    sys.exit(2)

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = SCRIPT_DIR.parent / "schema" / "handoff_package_schema.json"


def load_package(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # markdown 里的 YAML 代码块
    m = re.search(r"```ya?ml\s*\n(.*?)\n```", content, re.DOTALL)
    if m:
        content = m.group(1)

    stripped = content.strip()
    if path.endswith(".json") or stripped.startswith("{"):
        return json.loads(stripped)

    try:
        import yaml
        return yaml.safe_load(stripped)
    except ImportError:
        print("错误：YAML 解析需要 PyYAML。安装：python3 -m pip install pyyaml", file=sys.stderr)
        sys.exit(2)


def main():
    if len(sys.argv) != 2:
        print("用法: python3 validate_handoff.py <handoff_file>", file=sys.stderr)
        sys.exit(2)

    pkg_path = sys.argv[1]
    if not os.path.exists(pkg_path):
        print(f"错误：文件不存在 {pkg_path}", file=sys.stderr)
        sys.exit(2)

    if not SCHEMA_PATH.exists():
        print(f"错误：找不到 schema 文件 {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(2)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        package = load_package(pkg_path)
    except Exception as e:
        print(f"✗ 解析失败：{e}", file=sys.stderr)
        sys.exit(1)

    try:
        jsonschema.validate(instance=package, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"✗ 校验失败：{e.message}", file=sys.stderr)
        path_str = " / ".join(str(p) for p in e.absolute_path) or "(根)"
        print(f"  字段路径：{path_str}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ 校验通过：{pkg_path}")
    print(f"  source_skill : {package.get('source_skill')}")
    print(f"  target_skill : {package.get('target_skill')}")
    print(f"  material_count: {package.get('material_count')}")
    pending = package.get("upstream_summary", {}).get("pending_review")
    print(f"  pending_review: {pending}")
    sys.exit(0)


if __name__ == "__main__":
    main()
