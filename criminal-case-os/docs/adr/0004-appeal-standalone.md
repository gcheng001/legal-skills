# ADR 0004:救济阶段以独立 skill `criminal-appeal` 承载

> 状态:已通过(v3.3,2026-07-22)
> 决策背景:criminal-defense-workflow v3.1.0(外部,license: private)融合至 criminal-case-os v3.3 过程中,对一审判决后救济阶段(上诉/申诉/再审)的承载方式作出明确安排。

## 一、背景

criminal-case-os 在 v3.0(ADR 0001)中明确:一期边界排除二审、再审等救济阶段。该边界基于"OS 调度结构按诉讼阶段设计、避免摊薄一期深度"。

融合过程中,criminal-defense-workflow v3.1.0 提供 `sub-skills/11_上诉状撰写_SKILL.md` 与 `sub-skills/12_申诉与再审申请_SKILL.md` 两份高质量方法论文件(共 226 行内容)。完整吸收可显著增强 OS 救济阶段的处理能力。

## 二、决策

**救济阶段以独立 skill `criminal-appeal`(上诉状+申诉/再审申请两模块合一)承载,不纳入 criminal-case-os 调度。**

触发方式:**律师手动触发**(直接输入"上诉""申请再审"等关键词),加载全局规则等同 OS 调度。

## 三、理由

1. **维持 ADR 0001 边界**:救济阶段的程序性质(一审判决已作出)与一审阶段存在本质差异,继续纳入 OS 调度会摊薄一期深度,违背 ADR 0001 设计初衷。
2. **程序启动频率低**:相对一审/审查起诉的常规流程,上诉/再审仅在判决不利时启动,手动触发比 OS 调度更灵活。
3. **触发即加载全局规则**:独立 skill 不等于脱离 OS 治理——`criminal-appeal` SKILL.md 首部明确声明加载 redlines/soul/状态头/要件库等同 OS 调度。
4. **保持 OS 一期核心质量**:不为了"完整性"而牺牲一审阶段的处理深度。

## 四、影响

- **新增 skill**:`criminal-appeal`(`~/.shared-skills/criminal-appeal/SKILL.md`)
- **总控 SKILL.md**:
  - 调度表新增「救济阶段」节,明确不在 OS 调度内
  - 交互菜单新增第 14 项「上诉 / 申诉 / 再审」
  - 依赖清单登记
- **CONTEXT.md**:补充「救济阶段」术语定义
- **criminal-defense-statement / criminal-sentencing-defense**:最终产物附"如需上诉/再审,可触发 `criminal-appeal`"提示
- **case-archive**:归档清单新增上诉状/申诉状/再审申请书类别(见 `references/刑事归档清单.md`)

## 五、来源

criminal-defense-workflow v3.1.0:
- `sub-skills/11_上诉状撰写_SKILL.md`(原 license: private,作者署名已剥离)
- `sub-skills/12_申诉与再审申请_SKILL.md`(同上)

引入日期:2026-07-22
引入验证:汪欣案 A/B 对比测试中,B 组的「类案同判与重复计算论证」方法论标签可平移到上诉阶段
授权状态:**仅限内部使用,不得对外发布**

## 六、变更历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-07-22 | 初始版本,确立救济阶段独立承载安排 |