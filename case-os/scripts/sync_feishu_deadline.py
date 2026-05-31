#!/usr/bin/env python3
"""飞书多维表格 — 任务中枢同步脚本

调用本地 Node.js 脚本 sync-feishu-deadline.js 实现飞书写入。
凭证和表格ID已在 ~/.local/bin/sync-feishu-deadline.js 中配置。

## 模式

### 代理服务器模式（仪表盘直接调用）
```bash
python3 sync_feishu_deadline.py --server --port 18903
```
仪表盘点击「保存并同步→飞书」→ POST → 本代理 → node sync-feishu-deadline.js → 飞书API

### 直接模式（CLI）
```bash
# 从案件目录同步
python3 sync_feishu_deadline.py /path/to/case/dir
```"""

import argparse
import json
import os
import subprocess
import sys
import http.server
from pathlib import Path

NODE_SYNC_SCRIPT = Path.home() / ".local" / "bin" / "sync-feishu-deadline.js"
CACHE_FILE = Path.home() / ".cache" / "caseos-deadline-sync.json"


# ==================== 代理服务器 ====================

def run_server(port=18903):
    """启动本地 HTTP 代理，接收仪表盘 POST 请求，调用 Node.js 脚本同步"""

    class SyncHandler(http.server.BaseHTTPRequestHandler):
        def _cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_POST(self):
            cl = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(cl)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._cors_headers()
            self.end_headers()

            try:
                req = json.loads(body)
            except json.JSONDecodeError:
                self.wfile.write(json.dumps({"ok": False, "error": "Invalid JSON"}, ensure_ascii=False).encode())
                return

            action = req.get("action", "")
            if action == "sync_task":
                payload = req.get("payload", {})
                fields = payload.get("fields", {})

                # 保存到缓存文件
                CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CACHE_FILE, "w") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

                # 调用 Node.js 同步脚本
                task = fields.get("任务名称", fields.get("事项", ""))
                date = fields.get("截止日期", "")
                note = fields.get("备注", "")
                case = fields.get("来源案件", "")

                resp = call_node_sync(task, date, note, case)
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode())

            elif action == "ping":
                self.wfile.write(json.dumps({"ok": True, "message": "pong"}).encode())
            else:
                self.wfile.write(json.dumps({"ok": False, "error": f"Unknown action: {action}"}, ensure_ascii=False).encode())

        def do_OPTIONS(self):
            self.send_response(200)
            self._cors_headers()
            self.end_headers()

        def log_message(self, fmt, *args):
            print(f"  [{self.log_date_time_string()}] {args[0]}")

    server = http.server.HTTPServer(("127.0.0.1", port), SyncHandler)
    print(f"🔄 飞书同步代理已启动 → http://127.0.0.1:{port}")
    print(f"   仪表盘点击「保存并同步→飞书」即可直接写入")
    print(f"   按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 代理已停止")


def call_node_sync(task, date, note="", case=""):
    """调用 Node.js 脚本同步到飞书"""
    if not NODE_SYNC_SCRIPT.exists():
        return {"ok": False, "error": f"同步脚本不存在: {NODE_SYNC_SCRIPT}"}

    cmd = ["node", str(NODE_SYNC_SCRIPT), "--task", task, "--date", date]
    if note:
        cmd += ["--note", note]
    if case:
        cmd += ["--case", case]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ 飞书同步成功: {result.stdout.strip()}")
            return {"ok": True, "message": result.stdout.strip()}
        else:
            print(f"❌ 同步失败: {result.stderr.strip()}")
            return {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "同步超时（30秒）"}
    except FileNotFoundError:
        return {"ok": False, "error": "Node.js 未找到，请确认已安装 node"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ==================== CLI 入口 ====================

def main():
    parser = argparse.ArgumentParser(description="飞书多维表格同步工具（调用 Node.js 脚本）")
    parser.add_argument("--server", action="store_true", help="启动本地 HTTP 代理服务器")
    parser.add_argument("--port", type=int, default=18903, help="代理服务器端口 (默认 18903)")
    parser.add_argument("--task", "-t", help="任务名称")
    parser.add_argument("--date", "-d", help="截止日期 (YYYY-MM-DD)")
    parser.add_argument("--note", "-n", default="", help="备注")
    parser.add_argument("--case", "-c", default="", help="来源案件")

    args = parser.parse_args()

    if args.server:
        run_server(args.port)
    elif args.task and args.date:
        result = call_node_sync(args.task, args.date, args.note, args.case)
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if result.get("ok") else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
