---
name: labor-os
description: "劳动法OS 总控。菜单式路由与断点恢复,识别轨道(顾问/争议)与立场(三选一);自身不执行业务,只调度。TRIGGER when: 用户输入\"劳动法OS\"\"劳动OS\"\"劳动争议OS\"或由全局CLAUDE.md调度。"
---

# labor-os — 劳动法OS 总控

## 工作定位

**职责**:**统一入口与调度器**——三件事:
1. 加载红线与知识库索引(运行 `references/redlines-labor.md` + `references/workflow-labor.md` 链接);
2. 识别轨道(顾问 / 争议)与立场(争议轨三选一);
3. 断点恢复与调度。

**自身不执行业务**——所有实质工作派给 8 个子 skill。

---

## 菜单(必须首屏展示,触发后立即输出)

```
劳动法OS — 请选择服务:
【顾问轨】1 劳动合同设计/审查    2 规章制度设计/审查    3 离职方案    4 用工体检
【争议轨】5 新案接案审查        6 仲裁程序            7 裁审衔接    8 执行    9 继续已有案件
```

对应调度:
| 用户选择 | 调度 skill |
|---------|----------|
| 1 | `labor-contract-design`(询问 起草/审查) |
| 2 | `labor-policy-design`(询问 对象) |
| 3 | `labor-exit-plan` |
| 4 | `labor-audit` |
| 5 | `labor-intake` |
| 6 | `labor-arbitration` |
| 7 | `labor-bridge` |
| 8 | `labor-execution` |
| 9 | **断点恢复**(见下文) |

**排雷(写在 description 触发条件)**:
- "案件OS" 触发民事 case-os,与本 skill 无关;
- 裸词"仲裁" 触发 `labor-arbitration` 而非本 skill(本 skill 用于菜单/路由);
- 非劳动语境"合同审查" 触发 `contract-review` 而非本 skill。

---

## 断点恢复(选项 9 或用户说"继续")

### A 定位案件目录

询问用户/扫描案件路径:
- 案件根目录 = 用户给的路径 **或** 当前工作目录;
- 读 `案件目录/_archive/case-os-state.json`(**只读**) + `_archive/labor-os-state.json` + `案件目录/CLAUDE.md`;
- 任何一项缺失 → 当作**新案**,走 L1 接案审查;

### B 输出断点摘要

| 字段 | 来源 |
|------|------|
| 当前轨道(顾问/争议) | `labor-os-state.json.track` |
| 立场(claimant/respondent/adjudicator) | `labor-os-state.json.stance` |
| 时效状态 | `labor-os-state.json.limitation.status` |
| 仲裁进展 | `labor-os-state.json.arbitration.deadlines` |
| 最近产出 | `intermediate/劳动覆盖层/L{n}-{step}/` 最新文件 |
| 九步法进度 | `intermediate/原告九步法/`、`被告九步法/` 目录扫描 |

### C 待确认/拟继续清单

```
- ✅ 已完成: ...
- ⏳ 待确认: ...(黄底标注待用户决策的事项)
- ▶️ 拟继续: ...(下一步动作,推荐调度 skill)
```

### D 调度对应 skill

例如:`labor-os-state.json.workflow` 中:
- `l1_intake = completed` → 拟继续 `labor-arbitration`;
- `l2_arbitration = completed` 且 `arbitration.final_award != null` → 拟继续 `labor-bridge`;
- 等等。

### E 关键:九步法未完成时

争议轨案件若**九步法 S1-S9 未完成**:
- 提示用户:"本案件九步法未完成,劳动OS 不接管剩余九步法能力;"
- **提示由 case-os 流程继续**;
- 劳动知识注入依赖 **T7 提案: case-os 扩展点补丁**(由高澄人工套用)。

---

## 立场继承铁律

- 🟥 `labor-os-state.json.stance` 一经写入,**不得重复询问**;
- 🟥 立场为 `adjudicator` 时,**输出显著提示**:
  ```
  ⚠️ 裁判者模式已激活:保密隔离生效(本案件材料与分析禁止沉淀到顾问轨知识库或经验卡)
  ```
- 🟥 `adjudicator` 立场下,**双轨联动**(顾问/争议资源联动)禁用。

---

## 独立触发保障

子skill 偶尔会**被直接调用**(绕过本总控),此时必须**强制**先做:
1. 加载 `references/redlines-labor.md`;
2. 加载相关主题库索引;
3. 若为争议轨 — 尝试读 `labor-os-state.json`,继承 track/stance(缺失则问一次并写回);
4. 然后再进入本职流程。

(已在每个子 skill 的 SKILL.md "工作定位"段以"独立触发保障"标题落地)

---

## references/

| 文件 | 用途 |
|------|------|
| `redlines-labor.md` | 继承 case-os 红线 + 劳动新增红线(全文,各子skill引用) |
| `workflow-labor.md` | 双轨全景图 + 子 skill 一页纸 I/O |
| `knowledge/` | T2 产出的 10 个主题库(由 T9 收尾时复制入内) |

---

## 行数与验收

- 本文件:`< 200 行`,留 buffer 至 300;
- 菜单 9 项与 8 个子 skill 一一对应(选项 9 = 断点恢复);
- 含"独立触发保障"约定;
- 触发词描述排雷三条。

---

## 输出

**主调度产物**:
- 调度对应子 skill(派工);
- 产出摘要回到用户。

**断点恢复额外产物**:
- 案件断点摘要(交互输出,不落盘);
- `labor-os-state.json` 状态延续(若有)。

**菜单排版产物**:
- 菜单首屏输出后,**等待用户选 1-9** 才进入下一步;不得**自动**跑到某个子 skill。

---

## 知识引用

总控**自身不消费**知识库,只**调度**消费它的子 skill。
但菜单中**提示用户**:
- 争议轨:全程已固化到 `labor-arbitration` / `labor-bridge` / `labor-execution`;
- 顾问轨:已固化到 `labor-contract-design` / `labor-policy-design` / `labor-exit-plan` / `labor-audit`。

各子 skill 的"知识引用"段已列出所需主题库,不再在本文件内复制。
