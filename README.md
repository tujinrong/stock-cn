# stock-cn

**用完整AI提示词研究和管理的A股模拟投资辅助工程。** 用户确定意图与边界，AI综合资料决定买卖和仓位，通用工具负责取数、校验与文件记账；不把投资判断强制写成固定算法。

## 先看这三个文件

以A系列为例：

| 文件 | 用途 |
| --- | --- |
| [A/init.json](strategies/A/init.json) | 20万元初始化计划，五股各3万元、现金5万元；不等于已开账户 |
| [A/ai_input_template.md](strategies/A/ai_input_template.md) | 完整AI提示词：当前情况、去哪里查、如何判断、输出及当天文件处理 |
| [A/holdings.json](strategies/A/holdings.json) / [可读表](strategies/A/holdings.md) | 当前日期、总资产、现金、股票代码和股数；目前待初始化 |

## 全部系列入口

| 系列 | 策略 | 初始化 | 完整提示词 | 当前持仓 |
| --- | --- | --- | --- | --- |
| A | 现有五股组合管理 | [init](strategies/A/init.json) | [AI输入](strategies/A/ai_input_template.md) | [表格](strategies/A/holdings.md) |
| B | 备用 | — | [说明](strategies/B/prompt.md) | — |
| C | 固定五股池从现金择时 | [init](strategies/C/init.json) | [AI输入](strategies/C/ai_input_template.md) | [表格](strategies/C/holdings.md) |
| D | 优质股年度低位回升 | [init](strategies/D/init.json) | [AI输入](strategies/D/ai_input_template.md) | [表格](strategies/D/holdings.md) |
| E | 业绩改善 | [init](strategies/E/init.json) | [AI输入](strategies/E/ai_input_template.md) | [表格](strategies/E/holdings.md) |
| F | 异常下跌后回升买点 | [init](strategies/F/init.json) | [AI输入](strategies/F/ai_input_template.md) | [表格](strategies/F/holdings.md) |

[变体编号总表](strategies/README.md) · [共同提示词](strategies/common.md) · [输入/判断/落账契约](docs/ai-decision-contract.md) · [目录结构](docs/file-layout.md) · [数据主备](docs/data-sources.md) · [协作规范](AGENTS.md)

## 文件如何配合

`初始化计划（一次） → 当前持仓 → 完整提示词＋当次数据 → AI判断 → 交易校验 → 保存当天结果、更新当前持仓`。

每个系列下面放init.json、ai_input_template.md、holdings.json和holdings.md。实际运行后的daily/<日期>/保存完整输入、分析前持仓、AI判断、执行结果、分析后持仓和摘要，closing.json用于日结。事实事件在同系列trading/events/，测试账户在同系列simulations/<test_id>/<variant_id>/，不混正式资金。根trading与simulations现仅导航。

用户重点看到日期、初始资金、当前总资产、现金、各股票代码/名称/股数；可卖股数、成本与估值支持校验/绩效，技术版本集中在_meta。当前持仓不是每次重新套用初始15%权重。

## 当前实际状态

已建立A、C、D、E、F五个系列的初始化文件、完整提示词、持仓JSON和可读表，全部为草案/未初始化。A股数、日期与价格留null，不猜测；C–F计划全现金但尚无期初记账。B备用无账户，旧G只留迁移说明。

**尚未初始化、取得当前报价、生成成交、运行回放或建立后台任务。** 模板的动态填入、模拟撮合及每日自动更新还需后续实现。文件存在不表示工具已经运行或盈利。

## 已约定边界

每系列20万元总资产起点，可含多只股票；同系列变体独立测试但正式默认一个变体，不重复计算正式资金。A五股为招商银行、比亚迪、福耀玻璃、长江电力、恒立液压，初始股票75%+现金25%；C–F从全现金起步。

A股排除科创板，其他范围依已确认限制。每系列每天最多一次决策、至多一笔买入或卖出，不日内短线；正式用有效时段实际资料，测试可盘外按真实历史时点连续回放。两个月是评价例子，不是已开始考核或收益保证。

不用数据库，不保存原始行情库；持仓、成交、每日估值和必要证据在GitHub文件中追溯。AI自主选择研究方法，计算预算内复用未失效资料。确认后微调只向前生效，不重置账户或回写历史。

未来可并行分析不同策略，统一校验记账避免冲突；目前无后台运行器。仅保存项目模拟信息，不写用户真实账户/成本、个人资料或密钥。

## 既有离线演示

此前Python代码未改动，仍为简化账户、均线和规则分析器演示，不是真实自主研究模型。

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e ".[dev]"
stock-cn demo --cash 200000
pytest
```

演示不会应用新的init.json或更新新的持仓文件，不读取真实行情，也不创建每日任务。
