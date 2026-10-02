# 模拟运行与验证：0.4版

本轮已获用户授权开始编程和模拟测试。**仍不启用正式Paper Trading写账、券商下单或每日投资定时任务。** 已增加FORMAL受控预览适配器，用于证明与模拟模式同构；它不会持久修改正式账户。

## 已实现

- 从每系列init.json建立隔离账户；A的假定已有组合只记一笔期初事件，C–F从现金起步。
- 每天用最新持仓、现金、可卖股数、前次理由、选中变体和可用历史证据展开原有完整版提示词。
- AI通过文件答复，或显式选择的API适配器返回决定；程序不根据均线等规则替代AI选股。
- 单笔建议与实际Paper成交分开；SIMULATION与FORMAL预览共用decision契约和paper_core订单执行/账户更新函数，校验模式、身份、版本、时间、股票范围、金额、股数、可卖量、价格限制和每日额度。
- 十进制金额、逐日记账、连续持仓、净收益和日频回撤报告。
- 不同账户并发，同一账户按日期串行；有并发数、调用数和输入大小上限。
- 事件先保存，持仓和日文件由事件派生；可检测、恢复损坏的派生文件。事件损坏则停止，不篡改事实。

## 从哪里看

```text
strategies/A/holdings.json                 # 正式文件，本轮保持NOT_INITIALIZED
strategies/A/simulations/<test_id>/A02/
  manifest.json                           # 数据类型、范围、限制、提示词版本
  init.snapshot.json                      # 本测试初始化副本
  templates.snapshot.json                 # 原始项目提示词快照
  holdings.json                           # 模拟当前总资金、日期、现金、各股股数
  holdings.md
  requests/<日期>/ai_input.md              # 交给AI的实际完整输入
  requests/<日期>/attempts/                # 原始答复、校验反馈及修复输入
  daily/<日期>/
    ai_input.md                           # 实际成功答复所用提示词
    holdings_before.json
    decision.json                         # AI建议，不是成交
    execution.json                        # FILLED/REJECTED/NO_TRADE
    holdings_after.json
    research.json
    closing.json
    summary.md
  events/                                 # 唯一事实源与校验链
  validation.json
  report.md
runs/simulations/<test_id>/summary.md        # 跨策略汇总
```

模拟数据不进入各系列正式holdings.json。不会建设原始行情数据库。市场数据临时文件放仓库外；只保存必要输入、证据、成交/估值及结果。命令在本地克隆中生成文件后，需要提交Git才是GitHub持久记录；本仓库验证工作流会仅提交本次模拟目录，非强制推送，冲突时报错而不覆盖。

## 零付费工程验证

Python 3.11+，在仓库根目录执行：

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m stock_cn.sim_cli selfcheck --test-id smoke-001 --workers 2
```

默认7个变体：A01/A02/A03/C02/D02/E01/F01，每个回放5个虚拟交易日。selfcheck明确使用**合成价格和测试脚本回复**，验证买卖/持有分支、错误反馈、账户隔离和恢复。它不是量化策略，更不是AI投资收益证明。重复运行同一test_id不重复成交；改模板或数据应使用新test_id。

## 真正AI参与的文件交接

先通过probe或经过校验的其他来源取得仓库外数据文件。数据契约见sim_data.py；证据应有source、published_at、text，只把决策截止时点以前的资料交给AI。

```bash
python -m stock_cn.sim_cli probe --test-id source-001 --start 2025-08-01 --end 2025-08-08 --output /tmp/stock-cn-history.json
python -m stock_cn.sim_cli prepare --test-id research-001 --variant A02 --data /tmp/stock-cn-history.json --day 2025-08-04
```

打开该测试的requests/2025-08-04/ai_input.md，由ChatGPT等实际AI根据完整输入研究，将JSON答复保存为仓库外decision.json，再执行：

```bash
python -m stock_cn.sim_cli apply --test-id research-001 --variant A02 --data /tmp/stock-cn-history.json --day 2025-08-04 --decision /tmp/decision.json
```

Windows可用自己的仓库外临时路径替代/tmp/...。也可把各日回复放answers/A02/<日期>.json，用replay --agent files --answers <目录>继续。没有答复会报WAITING_FOR_AI，不伪造HOLD或自行买卖。

可选replay --agent openai适配器必须显式提供--allow-paid --model <模型ID>及环境变量OPENAI_API_KEY，并设置--max-calls。本轮不调用付费模型，也不保存密钥。历史回放不启用当前网页搜索；财务/公告/新闻须以历史已公开证据输入，防止把今天信息倒灌过去。这个适配器尚需在用户授权服务后进行真实模型验收。

## 自动改善的范围

默认一次格式修复机会，最多允许两次。在同一输入/同一决策内，把JSON缺字段、版本/日期错误等反馈给AI；每次提示词和答复均保留。网络超时不盲目重发付费请求。交易规则拒绝是当日最终结果，不改成另一笔订单重试。

```bash
python -m stock_cn.sim_cli audit --test-id smoke-001 --variant A02
python -m stock_cn.sim_cli audit --test-id smoke-001 --variant A02 --repair
```

--repair只能从完整事件重建派生的持仓、日文件和展示，不修改成交事实或策略。不自动提高仓位上限、改变目标、优化历史结果或升级正式变体。

## 当前验收边界

1. 当前实现是**日线模拟**：以前一交易日收盘资料判断，下一交易日开盘作模拟成交，再按该日收盘估值。不是历史11点回放；开盘执行时间是模拟设定，不是已取得精确逐笔时间。
2. 腾讯为日线主尝试、东方财富为备用；失败有记录，不保证免费接口持续可用。仅HTTP/日线连通性验收不能证明实时、财务、新闻或完整市场覆盖。
3. 第一版撮合只支持普通沪深主板、已提供的证券元数据。科创板始终排除；特殊证券/板块、ST、新股规则不猜测支持。涨跌停元数据缺失时拒绝成交，不能按演示10%规则冒充已核实规则。
4. 有分红、送转等权益事件的区间，在对应处理器完善前**阻止执行**；仅有日线但未核实权益事件的来源测试标FLOW_ONLY_REAL_PRICES，不作为投资绩效证据。
5. 原始日线获取不等于已经得到完整历史财报、新闻和年度研究窗口。预算默认只向AI注入最近10个已完成交易日收盘引用，其他研究证据须按需提供；不能以此宣称完成全年/全市场研究。
6. 目前没有正式11点持久运行器，也没有自动券商下单。已有FormalPaperSession用于LIVE_SNAPSHOT受控预览和模式同构测试；正式写账、实时源验收与定时触发仍未启用。真实AI策略好坏仍需在完整资料和合理对照下验证，工程测试通过不保证收益。

参考接口文档：AKShare官方股票数据文档 https://akshare.akfamily.xyz/data/stock/stock.html ；OpenAI Responses API https://developers.openai.com/api/reference/resources/responses/methods/create 。接口可用性以source-probe.json实际记录为准。


## 模拟到正式的平顺切换

详见 [mode-parity.md](mode-parity.md)。测试通过后不复制测试持仓或收益；只在用户确认后把已经验证的完整提示词版本标记为formal_prompt。正式账户重新按获确认的起点建立。模拟/正式共用decision JSON、交易约束、费用和账户更新核心，只替换历史时点数据与当前LIVE_SNAPSHOT数据适配器。
