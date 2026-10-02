# 正式模拟记录入口

按用户最新要求，持仓和每日结果统一放在各策略目录，本根目录只导航，不再创建trading/<系列>/account.json等第二套账本。

[全部系列持仓和AI输入](../strategies/README.md)。当前A/C/D/E/F的holdings.json已建立，但状态均为NOT_INITIALIZED；B备用，没有账户。没有实际成交或每日收益。

运行后每系列使用：

- strategies/<系列>/holdings.json：当前日期、总资产、现金、股数和版本。
- strategies/<系列>/holdings.md：可读持仓。
- strategies/<系列>/daily/<日期>/：实际输入、AI判断、执行、前后快照及摘要/日结。
- strategies/<系列>/trading/events/：事实事件；投影与快照一致提交。

AI建议先交易校验，有效模拟成交才改余额；HOLD、拒绝、数据不足和未运行分开。只保存项目模拟数据，不导入真实账户。详见[AI契约](../docs/ai-decision-contract.md)和[文件结构](../docs/file-layout.md)。
