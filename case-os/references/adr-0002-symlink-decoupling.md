# ADR-0002：case-os 全脚本脱钩 .codex/.claude 软链，自定位物理根

- **状态**：Accepted
- **日期**：2026-07-04
- **决策者**：高澄
- **关联**：ADR-0001（案件扫描根迁移）、CLAUDE.md「A 类 — 能力补丁」2026-07-04 条目

## 背景

case-os 历史上同时存在两个宿主目录的入口：`~/.codex/skills/case-os` 和 `~/.claude/skills/case-os`，两者都是软链指向物理目录 `~/.shared-skills/case-os/`，三处 inode 一致。同一份脚本通过任一软链调用都能跑、写到同一份 `data/`。

隐患是**软链清理**：CLAUDE.md 已标 Codex CLI 为「perceptible only, not callable」，迁移在进行中；主人清理 `~/.codex` 软链是迟早的事。一旦清理：

1. **5 个核心脚本**（`scripts/scan_case_folders.py`、`agents/weekly-scan/scan.py`、`agents/court-sms-monitor/monitor.py`、`scripts/case-post-step.sh`、`scripts/weekly_scan.sh`）原本通过 `~/.codex/skills/case-os/data/pending-files.json` 之类的硬编码定位 data 目录，软链一删立即断。
2. **3 个 launchd 部署脚本**（`scripts/deploy_portal.py`、`agents/weekly-scan/install.sh`、`agents/court-sms-monitor/install.sh`、`agents/agent_manager.sh`）硬编码 `~/.claude/skills/case-os/...` 生成 plist / 写日志 / 定位模板。
3. 文档（README.md / AGENT.md / MULTI_AGENT_REPORT.md）也有约 20 处 `~/.claude/skills/case-os/...` 路径示例，给主人的命令提示会误导。

风险等级：**中**——软链删除瞬间所有周期性 / 长驻进程失效，且失效模式为「找不到文件」静默退出，律师感知不到。

## 决策

**所有运行时代码必须通过自身位置定位物理根，不依赖任何 `~/.codex/skills/...` 或 `~/.claude/skills/...` 软链存活**。

### Python 模式

```python
from pathlib import Path
_SKILL_ROOT = Path(__file__).resolve().parent.parent  # resolve() 自动解析软链
DATA_DIR = _SKILL_ROOT / "data"
```

`Path.resolve()` 自 Python 3.6 起自动跟随所有软链到物理路径，无需 `-P` 标志。

### Shell 模式

```bash
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
CASE_OS_ROOT="$(cd -P "$SCRIPT_DIR/../.." && pwd -P)"  # install.sh 在 agents/<name>/ 时
# 或
CASE_OS_ROOT="$(cd -P "$SCRIPT_DIR/.." && pwd -P)"      # agent_manager.sh 在 agents/ 时
DATA_DIR="$CASE_OS_ROOT/data"
```

`-P` 关键：`cd` 和 `pwd` 默认是逻辑模式（保留软链），会得到 `~/.codex/skills/case-os` 这种字符串。`-P` 强制物理解析，得到 `~/.shared-skills/case-os`。

### 层级陷阱

`agents/<name>/install.sh` 的 `SCRIPT_DIR` 是 `agents/<name>/`，所以 `..` 得到 `agents/` 而非 case-os 根——必须 `../..`。这是改造过程中的真实 bug，已修复。`agents/agent_manager.sh` 在 `agents/` 直接，`..` 即 case-os 根。

### 部署到 launchd plist

plist 是 install.sh 用 heredoc 写入 `/Users/~/Library/LaunchAgents/` 的模板。改完后 plist 内的日志路径由 install.sh 在写盘时展开为绝对物理路径：

```xml
<key>StandardOutPath</key>
<string>~/.shared-skills/case-os/data/launchd-stdout.log</string>
```

launchd 直接读绝对路径，不解析 `$HOME`、不跟随软链，最稳。

### 文档（次要）

README.md / AGENT.md / MULTI_AGENT_REPORT.md 等 20 处 `~/.claude/skills/case-os/...` 路径示例**保留不动**——它们是给主人的命令提示，运行时无害。统一在 `references/adr-0002-symlink-decoupling.md` 与今日 daily 中说明"两条路径等价、任选其一即可"。

## 备选方案与取舍

- **直接换成 `~/.shared-skills/...` 硬编码**：放弃。物理目录将来可能再迁（如换 shared 策略、挪到外置 SSD）。硬编码即埋同样定时炸弹。
- **环境变量 `CASE_OS_ROOT`**：放弃。脚本必须 export 才能传递，对 launchd 长驻进程不友好（launchd 加载 plist 时环境极简）。
- **`realpath` / `grealpath`**：考虑过。`realpath` 在 macOS 自带，但语法稍繁；`cd -P && pwd -P` 是 bash 内置、可移植、无外部依赖，最终胜出。
- **新增共享 helper 模块**（`_skill_paths.sh`）：考虑过。三个脚本分布在不同目录，跨目录 source 需要稳定锚点，反而更脆弱。

## 后果

### 正向

- **软链死亡免疫**：主人清理 `~/.codex` 后，所有脚本仍能找到物理根，launchd plist 写的是绝对路径，新 install 出来的 plist 也能在清理后继续工作。
- **跨工具迁移零成本**：case-os 将来要从 `~/.shared-skills` 搬到 `~/Code/skills` 之类，**脚本一行不动**。
- **可移植性提升**：任何装到软链目录的 skill 都适用此模式，可作为 A 类规则固化（已在今日 daily 草拟）。

### 负向

- **`__file__` / `${BASH_SOURCE[0]}` 自定位在脚本被 `source` 时不可靠**：本批脚本都是 `bash script.sh` 直接执行，无 source 调用，不影响。
- **`cd -P` 后 `pwd` 输出绝对物理路径，复制粘贴体验略变**：可接受。
- **改完后已部署的旧 plist 仍在用 `$HOME/.claude/...` 路径**：launchd 实例继续跑（plist 已加载），但下次 install 才会更新——这是滚动升级的标准做法。

### 遗留

- **文档（README / AGENT / MULTI_AGENT_REPORT）20 处路径示例未改**：运行时无害，给主人的命令提示仍按字面敲能从软链调通，但**强烈建议主人在文档头部加一句"等价路径"` `~/.shared-skills/case-os` 一样可调"。
- **launchd plist 重新部署需要主人触发**：跑一次 `bash agents/weekly-scan/install.sh` 和 `bash agents/court-sms-monitor/install.sh`（或 `bash agents/agent_manager.sh restart`）即可滚动升级。本 ADR 范围内不动 launchd，等主人确认时机。

## 改动文件清单

| 文件 | 改动 |
|---|---|
| `scripts/scan_case_folders.py` | `Path(__file__).resolve().parent.parent` + `SCAN_ROOTS_FILE = _DATA_DIR / "scan-roots.txt"` |
| `agents/weekly-scan/scan.py` | 同上 |
| `agents/court-sms-monitor/monitor.py` | 同上 |
| `scripts/case-post-step.sh` | `SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` |
| `scripts/weekly_scan.sh` | 同上 |
| `scripts/deploy_portal.py` | `Path(__file__).resolve().parent.parent / "templates" / "evidence-portal.html"` |
| `agents/weekly-scan/install.sh` | `cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P` + `cd -P "$SCRIPT_DIR/../.." && pwd -P` |
| `agents/court-sms-monitor/install.sh` | 同上 |
| `agents/agent_manager.sh` | `cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P` + `DATA_DIR="$AGENTS_DIR/../data"` |