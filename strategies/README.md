# 策略、初始化、AI完整提示词与当前持仓

A、C、D、E、F为五个有效草案系列，B备用。**现在已能在每个系列目录下查看初始化文件、完整AI提示词和持仓文件。** 当前持仓均为NOT_INITIALIZED，不是已执行账户，股数/日期没有编造。

## 直接查看

| 系列 | 任务 | 初始化文件 | AI完整版提示词 | 当前持仓表 | 当前持仓JSON |
| --- | --- | --- | --- | --- | --- |
| A | 已有五股组合管理 | [init](A/init.json) | [完整提示词](A/ai_input_template.md) | [持仓表](A/holdings.md) | [JSON](A/holdings.json) |
| B | 备用，无账户 | — | [备用说明](B/prompt.md) | — | — |
| C | 固定五股池，从现金择时 | [init](C/init.json) | [完整提示词](C/ai_input_template.md) | [持仓表](C/holdings.md) | [JSON](C/holdings.json) |
| D | 优质股年度低位回升 | [init](D/init.json) | [完整提示词](D/ai_input_template.md) | [持仓表](D/holdings.md) | [JSON](D/holdings.json) |
| E | 业绩改善机会 | [init](E/init.json) | [完整提示词](E/ai_input_template.md) | [持仓表](E/holdings.md) | [JSON](E/holdings.json) |
| F | 异常下跌后的回升买点 | [init](F/init.json) | [完整提示词](F/ai_input_template.md) | [持仓表](F/holdings.md) | [JSON](F/holdings.json) |

## 当前变体编号

| 编号 | 名称 | 初始状态 | 长期意图与偏好 |
| --- | --- | --- | --- |
| A01 | 现有组合：稳健 | 五股75%＋现金25% | [A意图](A/prompt.md) · [A01](A/variants/A01.md) |
| A02 | 现有组合：均衡 | 同上 | [A意图](A/prompt.md) · [A02](A/variants/A02.md) |
| A03 | 现有组合：进取 | 同上 | [A意图](A/prompt.md) · [A03](A/variants/A03.md) |
| C01 | 固定股票池：稳健确认 | 全现金 | [C意图](C/prompt.md) · [C01](C/variants/C01.md) |
| C02 | 固定股票池：均衡择时 | 全现金 | [C意图](C/prompt.md) · [C02](C/variants/C02.md) |
| C03 | 固定股票池：机会优先 | 全现金 | [C意图](C/prompt.md) · [C03](C/variants/C03.md) |
| D01 | 年度低位：提前布局 | 全现金 | [D意图](D/prompt.md) · [D01](D/variants/D01.md) |
| D02 | 年度低位：回升确认 | 全现金 | [D意图](D/prompt.md) · [D02](D/variants/D02.md) |
| D03 | 年度低位：事件支持 | 全现金 | [D意图](D/prompt.md) · [D03](D/variants/D03.md) |
| E01 | 业绩改善：财报确认 | 全现金 | [E意图](E/prompt.md) · [E01](E/variants/E01.md) |
| E02 | 业绩改善：经营数据领先 | 全现金 | [E意图](E/prompt.md) · [E02](E/variants/E02.md) |
| E03 | 业绩改善：行业转折 | 全现金 | [E意图](E/prompt.md) · [E03](E/variants/E03.md) |
| F01 | 异常下跌：回升确认 | 全现金 | [F意图](F/prompt.md) · [F01](F/variants/F01.md) |

每系列20万元总资产起点，不是每只股20万元。A/C固定池：招商银行600036.SH、比亚迪002594.SZ、福耀玻璃600660.SH、长江电力600900.SH、恒立液压601100.SH；A假定已有组合，C只是候选池。A各股目标3万元，现金5万元；实际股数待起始时点和可靠价格换算。C–F计划20万元现金，初始化前不把计划当已记账现金。

同系列变体可独立测试但不同时盲写一个正式账户。正式默认一个active_variant；B不分配资金。所有变体仍DRAFT，未确认执行日期、风险边界和正式启用。

## 一次运行应当怎样留下记录

`init.json（仅一次） → holdings.json（最新状态） → ai_input_template.md（完整意图＋动态状态） → 当天ai_input.md → decision.json → 校验/模拟执行 → 当天前后快照＋更新holdings.json/holdings.md`。

每日文件在本系列daily/<日期>/，测试文件在本系列simulations/<test_id>/<variant_id>/。只有实际运行才生成日期记录，不预造交易。详见[AI契约](../docs/ai-decision-contract.md)和[目录设计](../docs/file-layout.md)。

继承[共同提示词](common.md)与[AGENTS](../AGENTS.md)：排除科创板、不做日内短线、每系列每天最多一次决策且至多一笔买入或卖出、真实资料、文件记账、测试/正式隔离、确认后向前微调。未来可新增G、H等，不改变现有系列含义；旧G为迁移说明，不参与运行。
