# stock-cn

A股模拟交易 + AI 分析实验工程。

目标是把 **A股交易规则、模拟账户、撮合、策略、AI分析、回测** 解耦，先做一个可离线运行的最小版本，后续可以接入 AkShare/Tushare、OpenAI API、数据库和 Web UI。

## 功能

- A股模拟账户：现金、持仓、可卖数量、盈亏
- 简化 A股交易规则：
  - 买入 100 股一手
  - T+1 卖出
  - 涨跌停校验（主板 10%、创业板/科创板 20%、ST 5%，可配置）
  - 佣金、最低佣金、卖出印花税、过户费
- 模拟撮合 Broker
- Strategy 策略接口
- AI Analyst 接口
- 回测/逐日模拟引擎
- 内置示例行情和均线策略，安装后即可运行
- pytest 测试

> 注意：这是研究与模拟工程，不连接真实券商账户，不构成投资建议。交易规则为可配置的工程化简化实现，实际交易前应以交易所、券商最新规则为准。

## 目录

```text
stock-cn/
├─ config/
│  └─ default.json
├─ src/stock_cn/
│  ├─ account.py
│  ├─ ai.py
│  ├─ broker.py
│  ├─ cli.py
│  ├─ domain.py
│  ├─ market.py
│  ├─ rules.py
│  ├─ simulator.py
│  └─ strategy.py
├─ tests/
│  └─ test_broker.py
├─ .gitignore
└─ pyproject.toml
```

## 快速开始

需要 Python 3.11+。

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
stock-cn demo
pytest
```

## 下一阶段建议

1. 接入 AkShare/Tushare 日线和实时行情。
2. 加 SQLite/PostgreSQL，保存行情、订单、成交、AI观点。
3. 接 OpenAI Responses API，把基本面、估值、技术面、新闻整理成结构化评分。
4. 增加你目前偏好的“年线低位 + 业绩稳定 + 谷底回升”策略。
5. 增加组合风险控制：单股上限、行业暴露、最大回撤、止损/减仓规则。
6. 做 Streamlit/FastAPI 页面，显示持仓、净值曲线和 AI 决策日志。
