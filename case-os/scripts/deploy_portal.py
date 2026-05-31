#!/usr/bin/env python3
"""deploy_portal.py — 部署证据门户到案件目录，注入真实案件数据。

用法:
  python3 deploy_portal.py <案件目录>

流程:
  1. 读取 intermediate/S0-证据卡片库.json
  2. 读取 intermediate/S0-证据关系.json
  3. 将数据注入 evidence-portal.html 模板
  4. __EMBEDDED__ = null → __EMBEDDED__ = {...}
  4. 输出到 案件目录/evidence-portal.html
  5. 打开浏览器
"""

import json
import os
import sys
import subprocess

TEMPLATE = os.path.expanduser("~/.claude/skills/case-os/templates/evidence-portal.html")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 deploy_portal.py <案件目录>")
        sys.exit(1)

    case_dir = os.path.abspath(sys.argv[1])
    for d in ['intermediate', '_archive']:
        p = os.path.join(case_dir, d)
        if os.path.isdir(p):
            break
    else:
        print(f"错误: 未找到 intermediate 或 _archive 目录: {case_dir}")
        sys.exit(1)

    # 读取证据卡片
    cards_path = os.path.join(case_dir, "intermediate", "S0-证据卡片库.json")
    rels_path = os.path.join(case_dir, "intermediate", "S0-证据关系.json")

    cards = []
    if os.path.exists(cards_path):
        with open(cards_path) as f:
            cards = json.load(f).get("cards", [])
    rels = []
    if os.path.exists(rels_path):
        with open(rels_path) as f:
            rels = json.load(f).get("relations", [])

    # 注入数据到模板
    payload = json.dumps({"cards": cards, "relations": rels}, ensure_ascii=False)

    with open(TEMPLATE) as f:
        html = f.read()

    html = html.replace('var __EMBEDDED__ = null', 'var __EMBEDDED__ = ' + payload)

    out_path = os.path.join(case_dir, "evidence-portal.html")
    with open(out_path, "w") as f:
        f.write(html)

    rels_count = len([r for r in rels if r.get("status") != "rejected"])
    print(f"✅ 证据门户已部署: {out_path}")
    print(f"   注入 {len(cards)} 条证据, {rels_count} 条关系")

    # 打开
    subprocess.run(["open", out_path], check=False)

if __name__ == "__main__":
    main()