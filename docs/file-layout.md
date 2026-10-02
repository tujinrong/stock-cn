# 纯文件结构：每个策略下直接查看提示词、持仓和日结

最新约定：将当前持仓与正式/测试数据集中在`strategies/<系列>/`。此版替代旧文档的根`trading/<系列>/account.json`和根`simulations/<test_id>/.../account.json`写入路径，不保留两套可写余额。旧目录只作导航。

## 1. 目录

```text
stock-cn/
├── AGENTS.md
├── README.md
├── docs/
│   ├── ai-decision-contract.md          # 初始化/AI输入/判断/落账契约
│   ├── file-layout.md                   # 本文件
│   ├── data-sources.md                  # 数据来源主备与验收
│   └── requirements-before-file-layout.md # 历史需求，只作追溯
├── strategies/
│   ├── README.md                        # 可点击的统一入口
│   ├── index.json                       # 系列/变体和文件路径，不是账户
│   ├── common.md                        # 共同投资约束
│   ├── A/
│   │   ├── init.json                    # 20万元期初配置，未执行
│   │   ├── prompt.md                    # 五股组合长期意图
│   │   ├── ai_input_template.md         # AI完整提示词，动态填当次数据
│   │   ├── holdings.json                # 唯一当前持仓，现为待初始化
│   │   ├── holdings.md                  # 同版本可读持仓表
│   │   ├── variants/A01.md A02.md A03.md
│   │   ├── daily/                      # 以下为运行后生成
│   │   │   └── YYYY-MM-DD/
│   │   │       ├── ai_input.md          # 已展开、实际用过的提示词
│   │   │       ├── holdings_before.json
│   │   │       ├── research.json
│   │   │       ├── decision.json
│   │   │       ├── execution.json
│   │   │       ├── holdings_after.json
│   │   │       ├── closing.json         # 收盘估值，非盘中交易
│   │   │       └── summary.md
│   │   ├── trading/events/<event_id>.json
│   │   └── simulations/<test_id>/<variant_id>/
│   │       ├── manifest.json           # 模式、区间、版本和实际完成范围
│   │       ├── init.json               # 此测试采用的初始化计划快照
│   │       ├── holdings.json           # 此变体自己的连续账户
│   │       ├── holdings.md
│   │       ├── events/
│   │       └── daily/YYYY-MM-DD/        # 同样的当日文件结构
│   ├── B/prompt.md                      # 备用，无账户和运行文件
│   └── C/ D/ E/ F/                     # 与A同结构，可持多股
├── trading/README.md                    # 旧根目录导航，不再写第二账本
├── simulations/README.md                # 旧根目录导航
├── runs/                               # 批次/尝试状态，非余额或成交源
├── reports/                            # 从策略账本汇总的报告和CSV
└── src/ config/ tests/ .github/         # 既有离线演示，本轮未改代码
```

本轮已创建五个有效系列的init、完整模板、holdings.json和holdings.md。日期目录、事件、测试账户、实际提示词快照和日结只有运行后才创建，不能用占位文件伪造成绩。

## 2. 编号与资金

A=现有五股组合；B备用；C=固定五股池从现金择时；D=年度低位回升；E=业绩改善；F=异常下跌回升。一个系列是一个投资任务/资金池，可以持多股，不是一只股票。未来新增方案从G起，废弃G说明不参与运行。

每个正式系列初始总资金默认20万元；A股票目标75%（五股各15%）+现金25%，C–F全现金，B不建账户。init.json是当前初始化计划的唯一详细来源，index.json仅指向它；日常holdings.json是当前账户，不从init每日恢复。

同系列对照变体各有独立测试起点，但不能把多个变体当额外正式出资。正式默认一个active_variant管理系列账户。测试路径区分test_id和variant_id，不能覆盖同系列正式文件。

## 3. 数据与提示词

用户关注的核心是日期、总资金/当前总资产、现金、股票代码和股数。成本、估值、可卖股数用于收益/可执行性；_meta集中少量版本与时间字段，避免把主表做得复杂。字段含义见[AI契约](ai-decision-contract.md)。

完整版包含完整投资目标、变体偏好、查询网站与方向、持仓上下文、输出格式及当天文件处理；只有实际日期/账户/证据是动态变量。真正运行保存已展开ai_input.md与input_commit、input_revision及来源版本，不能只留会变化的文件路径。

未初始化的null不代表0，股票池不代表持仓。金额按十进制规则计算，数量为整数，代码保留前导零和市场后缀，时间带时区。初始价格必须有来源；A假定期初已持有，不假造五笔当日交易。

## 4. 事实与一致记账

事件为事实源；holdings.json、Markdown表、日快照及汇总CSV是可重建投影。交易、结算、分红、估值和修订要区分。旧事件不静默删除；更正追加有引用的纠正事件。真实净值要包括现金、浮动盈亏和费用。

一个有效决策的事件、执行结果、前后快照、当前持仓和摘要一致提交，只有确认成功才说已保存。使用模式/系列/账户/市场日期/decision_id去重；版本只前进。并发写main须重读最新版本、串行合并并非强制提交，不能把JSON中的lock字段当互斥锁。

当天已完成HOLD/交易拒绝不能重新择时，技术取数失败可以恢复同一次尝试但先查已有结果。没有运行、数据不足、AI决定不动和已成交必须分别显示。收盘价缺失可暂估并说明，不把盘中数据伪作收盘。

## 5. 异步与测试

批次状态在runs/<batch_id>/manifest.json及jobs/<job_id>/status.json，使用QUEUED/RUNNING/COMPLETED/FAILED/SKIPPED/CANCELLED；状态不是成交账本。COMPLETED不代表一定交易。

未来可并行研究不同策略/隔离变体；同账户各历史日必须按前日余额顺序推进。共同资料可以在相同信息截止时点只读复用，但不能让未来资料污染回放。提交成交前重核报价、时段、账户和策略版本。一个策略失败不应令其他策略结果虚构或无限挂起。

并发数、超时、费用预算和定时部署还待授权及验收，文件存在不代表后台运行已实现。没有实际任务不承诺定时执行。本轮没有新增代码、调度、付费服务或模拟交易。

## 6. 留存与安全

不用数据库，不长期保存全市场K线、盘口、逐笔流或新闻全文。允许临时取数；保存必要来源时间、证据、初始化快照、模拟成交、每天净值即可。仅承诺按已保存记录追溯，不保证还原每次完整市场快照或同一AI输出。

临时策略可在某系列的隔离测试下使用，不能自动成为正式策略。重跑使用新test_id、保留旧结果；报告仅统计实际完成区间，不把历史模拟和正式前向记录拼接。

根reports汇总各系列结果，不形成另一个账户。仓库可能公开，仅保存本项目模拟资料，不导入用户真实持仓/成本、个人信息、凭证或受限制数据。后续分年归档另约定，不擅自清理历史。
