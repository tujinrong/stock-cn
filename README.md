# stock-cn

**意图驱动、GitHub纯文件记账的A股AI模拟辅助工具。** 策略不是固定买卖公式；AI决定研究与仓位，程序负责可靠的输入、校验和记录。

## 当前版本：0.4模拟执行版

用户已授权开始编程与模拟测试。新增模拟引擎、完整提示词装配、AI文件交接、可选API适配器、多账户并发、校验与派生文件修复。正式持仓不变，未启用每日投资调度或真实券商交易。

| 内容 | 入口 |
| --- | --- |
| **运行、测试、AI交接与限制** | [模拟运行指南](docs/simulation-guide.md) |
| **所有策略、完整提示词、当前持仓** | [策略导航](strategies/README.md) |
| A系列完整AI提示词 | [A/ai_input_template.md](strategies/A/ai_input_template.md) |
| 初始化/判断输出契约 | [AI与文件契约](docs/ai-decision-contract.md) |
| 校验批次结果 | [runs/simulations/](runs/simulations/) |
| 自动验证工作流 | [.github/workflows/simulation-validation.yml](.github/workflows/simulation-validation.yml) |
| 项目边界 | [AGENTS.md](AGENTS.md) |

## 先运行无付费自检

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m stock_cn.sim_cli selfcheck --test-id smoke-001 --workers 2
```

自检使用**TEST_ONLY合成价格＋测试脚本回复**。它证明工程流程和资金计算是否符合测试，不证明AI策略盈利。真正AI参与用prepare生成输入、apply接收AI答复，或在单独授权后选择API适配器；见运行指南。

模拟结果放strategies/<系列>/simulations/<test_id>/<variant>/，不覆盖strategies/<系列>/holdings.json。每天保存实际输入、决策、执行结果、前后持仓和日结。原始行情不建库。

自动验证工作流运行单元测试及仓库实际提示词的多变体模拟，有限尝试历史日线主备源，并只提交模拟结果。没有日程触发器，也不调用付费模型。网络验收失败会单独记录，不能把其他测试通过说成数据源通过。

## 策略与资金

A为已有五股组合，A01稳健/A02均衡/A03进取；B备用；C固定股票池从现金择时；D年度低位回升；E业绩改善；F异常下跌回升。每系列计划20万元，平行变体测试不重复计算正式资金。

A初始目标五股各15%、现金25%，实际整数股取整余款留现金。其他系列现金起步。所有系列排除科创板，每个账户每个交易日最多一笔买入或卖出，也可以不动，不做日内短线。

## 尚不能据此声称完成的内容

当前日线回放不是历史11点逐笔回放；财务/新闻和年度研究资料需要真实时点证据，不是读取日线即可完成。特殊交易规则和权益事件处理仍需完善，缺失时拒绝或明确降级，不猜测成交。API适配器没有在未授权情况下调用真实付费模型。两个月盈利能力、全市场选股效果与正式实时执行尚未验证。

原有stock-cn demo是旧离线均线演示，与新的AI模拟接口分开保留。

> 本项目只做模拟。测试收益不构成收益承诺，不保存真实券商账户、个人信息或密钥。
