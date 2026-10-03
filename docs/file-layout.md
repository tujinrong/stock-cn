# GitHub纯文件结构：策略、研究、判断、交易与续跑

本项目不用数据库。**每个变体是独立执行单元**，策略系列只是分组。正式Paper账户、模拟账户、研究状态、提示词版本和历史评价都由GitHub文件保存；原始全市场行情不长期入库。

## 1. 主目录

```text
stock-cn/
├── AGENTS.md
├── README.md
├── config/
├── docs/
│   ├── ai-decision-contract.md
│   ├── ai-select-candidate-pipeline.md
│   ├── data-sources.md
│   ├── decision-research.md
│   ├── research-input-files.md
│   ├── file-layout.md
│   ├── mode-parity.md
│   ├── simulation-guide.md
│   └── time-travel.md
├── strategies/
│   ├── index.json
│   ├── common.md
│   ├── A/ C/ D/ E/ F/
│   │   ├── prompt.md                 # 系列投资意图
│   │   ├── ai_input_template.md
│   │   ├── init.json
│   │   └── variants/
│   │       └── D02/
│   │           ├── prompt.md         # 该变体完整基线提示词
│   │           ├── prompt_versions/  # v000/v001...
│   │           ├── simulation_prompt.json
│   │           ├── formal_prompt.json
│   │           ├── improvement_state.json
│   │           ├── init.json
│   │           ├── holdings.json     # 该变体唯一FORMAL Paper账户
│   │           ├── holdings.md
│   │           ├── research_state.json   # AI_SELECT正式研究状态
│   │           └── simulations/
│   │               └── <test_id>/    # 独立模拟连续账户
│   │                   ├── events/
│   │                   ├── holdings.json
│   │                   ├── holdings.md
│   │                   ├── manifest.json
│   │                   ├── research_state.json
│   │                   ├── requests/
│   │                   └── daily/
│   └── B/                         # 备用系列
├── research-requests/
│   ├── universe/                  # 全市场候选数据源探测请求
│   └── evidence/                  # CNINFO官方公告探测请求
├── research-job-requests/         # 请求AI财务/新闻研究任务包
├── research-answers/              # AI财务/新闻研究答案
├── research-inputs/
│   └── <variant>/YYYY-MM-DD/      # 已校验、决策可直接读取的研究资料
│       ├── manifest.json
│       ├── candidate-research-pack.json
│       ├── universe-scope.json
│       ├── official-disclosure-pack.json
│       ├── financial-reviews.json
│       └── news-research.json
├── research-decision-requests/    # 无未来成交价的研究决策输入请求
├── research-decision-answers/     # BUY/SELL/HOLD判断答案
├── research-execution-requests/   # 检查真实下一交易日是否已出现
├── evaluation-plans/              # 历史AI评价计划
├── evaluation-answers/
├── evaluation-score-requests/
├── prompt-improvement-requests/
├── runs/
│   ├── research/
│   │   ├── universe/
│   │   ├── evidence/
│   │   └── jobs/
│   ├── research-decisions/
│   ├── evaluations/
│   ├── prompt-improvements/
│   └── simulations/
├── reports/
│   └── performance/
├── src/stock_cn/
├── tests/
└── .github/workflows/
```

## 2. 一个AI_SELECT判断的完整文件链

以D02/F01为例：

1. **宽市场轻筛**：东方财富主源，新浪备用；当前支持的沪深普通主板，排除科创板，当前实现也不开放创业板。
2. **有限候选深查**：只给约30～60个轻筛种子分配历史K线预算，再缩到少量深查候选；轻筛排名不是推荐。
3. **官方资料**：CNINFO保存公告元数据和正式报告引用，不把公告标题自动解释成利好/利空。
4. **AI研究任务**：`runs/research/jobs/<job_id>/`保存当时资料和AI研究任务；AI输出财务复核和新闻研究。
5. **研究输入**：验证通过后写入`research-inputs/<variant>/<date>/`。未来信息、非官方财务来源、股票范围冲突会被拒绝。
6. **研究决策**：`runs/research-decisions/<test_id>/<variant>/<date>/`保存完整提示词、账户、时光穿越资料和锁定BUY/SELL/HOLD。
7. **判断锁定**：`decision.lock.json`保存prompt/decision哈希；锁定后不再因后续涨跌修改判断。
8. **延迟执行**：若下一真实交易日尚未存在，只写`execution-attempts/<date>.json`的WAITING；不伪造开盘价。
9. **真实下一交易日出现后**：只使用第一个真实交易日开盘价，通过同一Paper交易核心生成`execution.json`、`holdings_after_execution.json`和`continuation.json`。
10. **连续续跑**：`continuation.json`可以初始化新的隔离连续模拟账户，保留现金、股数、成本和费用，不重置20万元。

FORMAL账户从不被上述历史/研究流程修改。

## 3. 每个变体自己的提示词与账户

当前执行单位是`VARIANT`。例如D02：

```text
strategies/D/variants/D02/
├── prompt.md
├── prompt_versions/v000.md
├── prompt_versions/v001.md
├── simulation_prompt.json
├── formal_prompt.json
├── improvement_state.json
├── init.json
├── holdings.json
├── holdings.md
├── research_state.json
└── simulations/
```

`simulation_prompt.json`可以指向稳定性改进后的版本；`formal_prompt.json`必须经过单独确认才可提升。提示词自动改进最多10轮，只改格式、时间边界、候选解释、资料缺口等稳定性问题，**不能用未来收益自动优化投资判断**。

D02和F01已经完成第1轮稳定性改进（v001）；正式prompt仍为v000，未自动提升。

## 4. 账户与交易事实

- 每个变体默认独立20万元模拟起点。
- A系列可按五股+现金配置初始化；C/D/E/F从现金开始。
- FORMAL账户在`strategies/<series>/variants/<variant>/holdings.json`。
- 模拟连续账户在该变体自己的`simulations/<test_id>/`。
- 一天最多一个完成的BUY/SELL/HOLD决策，最多一笔交易；不能同日卖一只再买另一只。
- T+1、资金、整手、涨跌停、停牌、费用、报价时间等由程序层校验。
- 有效成交才改变股数/现金；研究文件、AI建议、报价参考都不直接改账户。
- FORMAL当前仍是Paper Trading设计，未连接券商。

## 5. 历史评价与未来信息隔离

`runs/evaluations/<eval_id>/`使用两阶段：

- 阶段A：时光穿越到历史时点，生成AI输入并锁定判断；
- 阶段B：判断锁定后才读取未来5/20/40交易日价格评分，并与HOLD反事实比较。

未来结果不进入当天AI输入，也不进入PromptLab自动改进。遇到疑似除权/送转价格断点时，相关区间标记不可可靠评分，不用错误的未复权收益评价判断。

## 6. 当前真实联调状态

已完成的真实源验证包括：

- 全市场当前普通主板候选：东方财富主、运行环境失败时新浪备用；
- 候选历史日线：腾讯主、东方财富备用；
- CNINFO官方公告与定期报告引用；
- D02/F01的2026-09-30研究输入、完整AI判断和decision lock。

2026-09-30锁定结果：

- D02：BUY恒瑞医药300股，约7.1%拟仓位；**尚未成交**。
- F01：HOLD，100%现金。
- 截至2026-10-03的真实数据检查，两者均为`WAITING_FOR_REAL_NEXT_SESSION_DATA`，没有伪造成交。

## 7. 数据留存与安全

不长期保存全市场原始行情、逐笔、盘口和新闻全文。保存必要的：

- 候选与研究摘要；
- 数据来源、发布时间、获取结果和失败原因；
- 官方报告引用与AI财务复核；
- 完整AI输入和decision；
- 模拟成交、持仓、日结和绩效；
- prompt版本、哈希和审计记录。

仓库为公开项目时，不写真实券商账号、密钥、个人信息或真实私密持仓。
