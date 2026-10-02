# stock-cn

**用自然语言提示词管理的 A 股 AI 模拟投资工程。** 用户确定投资意图与边界，AI 自主研究、判断买卖和仓位；通用工具负责取数、规则校验与记账，不把投资判断写成固定处理流程。

## 从这里查看

| 内容 | 入口 |
| --- | --- |
| 策略编号总表 | [strategies/README.md](strategies/README.md) |
| 所有策略共同提示词 | [strategies/common.md](strategies/common.md) |
| 招商银行提示词及变体 | [策略 A](strategies/A/prompt.md) · [A01](strategies/A/variants/A01.md) · [A02](strategies/A/variants/A02.md) · [A03](strategies/A/variants/A03.md) |
| 比亚迪提示词及变体 | [策略 B](strategies/B/prompt.md) · [B01](strategies/B/variants/B01.md) · [B02](strategies/B/variants/B02.md) · [B03](strategies/B/variants/B03.md) |
| 自主选股与组合草案 | [策略 C](strategies/C/prompt.md) · [策略 D](strategies/D/prompt.md) · [策略 E](strategies/E/prompt.md) |
| 目录与文件记账设计 | [docs/file-layout.md](docs/file-layout.md) |
| 行情与资料来源方案 | [docs/data-sources.md](docs/data-sources.md) |
| 正式模拟交易记录 | [trading/README.md](trading/README.md) |
| 调试与历史模拟 | [simulations/README.md](simulations/README.md) |
| 异步任务与批次 | [runs/README.md](runs/README.md) |
| 收益汇总 | [reports/README.md](reports/README.md) |
| 项目协作规范 | [AGENTS.md](AGENTS.md) |

## 已确定的边界

支持 N 个独立策略，每策略初始模拟资金20万元；A、B等为策略，A01、B02等为变体。正式默认每策略一个变体，对照实验独立记账，不重复计算资金。

FIXED 固定股票和 AI_SELECT 自主选股均由 AI 综合最新可得行情、财务、公告及新闻，围绕约定区间的净收益与损失/回撤决定买卖和仓位。两个月为评价区间例子，不是已开始考核；过去一年研究窗口不等于必须持有一年。

每策略每交易日最多一次买入或卖出，也可不操作；不是买一次再卖一次。正式判断在有效交易时段进行；调试与历史回放可盘外运行，优先使用真实历史资料，按当时可知信息和虚拟日期推进。正式与测试收益完全分开。

**不用数据库。所有策略、账本、日结和模拟结果以 GitHub 文件管理。** 原始行情按需临时读取，不建立本地行情库；关键成交价、每日估值、证据来源、提示词版本与账户状态必须保存。

未来支持多个策略后台异步分析、独立完成和统一汇总；同账户按时序推进，账本提交防重复、防冲突。正式策略可经对话明确授权或用户确认微调，只向前生效，不重置资金或历史收益。

## 目前实际完成的内容

已建立可浏览的目录入口、15个候选变体的 Markdown 提示词草案、纯文件记账与后台异步设计。策略索引全部为 DRAFT、enabled=false、active_variant=null。

**策略尚未确认，未开始新策略编程，未开启后台任务、模拟交易或两个月回放。** trading/、simulations/、runs/、reports/ 当前只含使用说明，没有伪造的账户或成绩。

此前 Python 代码仍为离线演示：简化账户、撮合和交易规则、均线策略、规则分析器占位、命令行和测试。它尚不具备本设计全部能力；RuleBasedAIAnalyst 不是自主研究模型。本项目不连接真实券商。

## 当前文件导航

```text
stock-cn/
├── AGENTS.md
├── docs/                       # 目录/记账/取数设计及此前需求
├── strategies/                 # 共同提示词、索引、A–E策略及编号变体
├── trading/                    # 正式模拟事件、账户及逐日日结
├── simulations/                # 临时测试、历史回放及独立结果
├── runs/                       # 批次、任务状态及尝试记录
├── reports/                    # 汇总报告、净值/交易CSV
├── config/default.json         # 既有演示配置，并非已启用正式账户
├── src/stock_cn/                # 既有离线演示，暂不改造
├── tests/
├── .github/workflows/test.yml  # 既有代码测试，不是投资定时任务
└── pyproject.toml
```

## 仅运行既有离线演示

需要 Python 3.11+。

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e ".[dev]"
stock-cn demo --cash 200000
pytest
```

演示不建立持久正式账户、不读取真实历史或实时数据、不启动每日任务。待策略确认后，再按需要编写通用工具并进行取数、并发、记账与收益校验。

> 仓库可能公开，仅保存项目模拟资料，不写真实券商账户、真实持仓、个人资料或密钥。投资研究与历史模拟均不构成收益承诺。
