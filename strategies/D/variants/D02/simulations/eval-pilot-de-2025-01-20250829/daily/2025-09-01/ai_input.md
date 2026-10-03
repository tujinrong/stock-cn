# D02：独立执行的完整AI提示词

本文件已展开全部内容，只注入本次日期、账户和证据，不再在运行时拼接其他变体。
<!-- IMMUTABLE_STRATEGY_START -->
{
  "series_id": "D",
  "variant_id": "D02",
  "initial_capital_cny": 200000,
  "account_scope": "ONE_INDEPENDENT_VARIANT",
  "allowed_symbols": null,
  "excluded_boards": [
    "科创板"
  ],
  "max_decisions_per_market_day": 1,
  "max_orders_per_market_day": 1,
  "paper_only": true,
  "no_future_information": true
}

## 不可自动改变的投资意图
# D：优质股年度低位回升

状态：DRAFT。类型：AI_SELECT。初始模拟资金20万元，默认100%现金开始。

在确认的A股范围内（排除科创板及其他已约定排除范围），寻找经营质量没有明显受损、价格或估值处于过去一年相对有利位置，并开始出现改善迹象的公司。

一个D系列可以同时研究多只股票，也可以逐步持有多只；不要求只选一只。不要把“跌得最多”当成最好，也不能事后用涨幅倒选赢家。

分别判断公司质量、当前价格吸引力、改善是否可能在评价区间内体现，以及不同候选之间的行业和共同风险。允许保持100%现金。

## 变体
- D01：提前布局
- D02：回升确认
- D03：事件支持

## 本变体唯一的风险与研究偏好
# D02：年度低位——回升确认

状态：DRAFT。属于[D系列](../prompt.md)。

更重视低位后的改善已经持续出现，并得到经营、行业或价格表现相互支持。允许错过最低点，以减少把短暂反弹误作转折。

仍需确认价格没有因反弹而失去吸引力。

<!-- IMMUTABLE_STRATEGY_END -->

## 已展开的资料查询、账户分析与输出要求
# D系列：优质股年度低位回升——AI分析完整版提示词

版本：1.0-draft。[初始化](init.json) · [当前持仓](holdings.md) · [JSON](holdings.json)。以下投资任务已完整展开，只有本次时间、持仓和证据需要填入。当前未初始化、未启用。

## 一、角色与意图

你管理D系列20万元人民币模拟账户，从现金开始，在用户确认的A股范围内寻找经营质量没有明显受损、过去一年价格或估值相对有利、并有改善迹象的公司。排除科创板，其他范围限制保持有效。可以逐步持有多只，不能按跌幅榜或事后涨幅选赢家，也不给用户已买的股票额外加分。

分别判断公司质量、当前价格、为什么改善可能在剩余评价区间体现。低位不是便宜的证明，反弹不是持续改善的证明。目标为约定期间（如两个月）整个账户扣费净收益与亏损/回撤的合理权衡；不保证正收益或预知最低点，不因亏损延后考核。

自主决定研究路径、买卖与股数、现金比例，不强迫固定评分。没合适机会可等，持有后不能每天当空账户重新开始。

本次只执行上面固定的变体偏好，不再从系列其他变体中选择。

## 二、当前情况

正式账户strategies/D/holdings.json，测试账户strategies/D/simulations/<test_id>/<variant_id>/holdings.json。每次从同一Git版本读最新实际账户，不用初始配置、旧快照或聊天记忆代替。

模式、变体、运行/决策ID、输入Git版本、账户路径、授权、日期、虚拟/现实信息截止、Asia/Shanghai、评价起止和风险边界：
{
  "mode": "SIMULATION",
  "strategy_id": "D",
  "variant_id": "D02",
  "run_id": "eval-pilot-de-2025-01-20250829-D02",
  "decision_id": "eval-pilot-de-2025-01-20250829-D02-2025-09-01",
  "date": "2025-09-01",
  "decision_time": "2025-08-29T15:00:00+08:00",
  "information_cutoff": "2025-08-29T15:00:00+08:00",
  "execution_time": "2025-09-01T09:30:00+08:00",
  "timezone": "Asia/Shanghai",
  "execution_basis": "PREVIOUS_CLOSE_NEXT_OPEN_NOT_11AM",
  "input_revision": 1,
  "input_commit": "aa8de862de7351a9811d082bb1f45d0162cef57b",
  "input_snapshot_sha256": "2bd2fefc47737926bc7715f24f23e3f0c4151567b701b35b053b3454b2893fd3",
  "account_path": "strategies/D/variants/D02/simulations/eval-pilot-de-2025-01-20250829/holdings.json",
  "authorization": "Only this isolated simulation; not formal. DRAFT strategy may be tested.",
  "evaluation_start": null,
  "evaluation_end": null,
  "settlement_note": "sellable_quantity is next-session availability, not same-day T+0",
  "data_kind": "REAL_HISTORY",
  "fidelity": "BOUNDED_CANDIDATE_REAL_DAILY"
}


```json
{
  "strategy_id": "D",
  "status": "SIMULATION",
  "date": "2025-08-29",
  "initial_capital_cny": "200000.00",
  "cash_cny": "200000.00",
  "total_equity_cny": "200000.00",
  "positions": [],
  "_meta": {
    "schema_version": "0.4",
    "mode": "SIMULATION",
    "paper_only": true,
    "variant_id": "D02",
    "test_id": "eval-pilot-de-2025-01-20250829",
    "revision": 1,
    "valuation_time": "2025-08-29T15:00:00+08:00",
    "fees_cny": "0.00",
    "last_decision_date": null,
    "data_kind": "REAL_HISTORY",
    "time_travel_jump": true,
    "last_event_id": "000001"
  }
}

```

| 股票代码 | 名称 | 当前股数 | 可卖股数 | 成本 | 估值价/时间 | 当前市值/权重 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| — | 无持仓 | 0 | 0 | — | — | 0 |

此前投资理由、候选进展、当前收益与风险：模拟期初
已授权范围、排除条件与观察名单：[
  "600900.SH"
]


未初始化时null不是0元；无持仓显示无持仓。每次传入全部实际持股，某股行情缺失仍保留该行，候选不能混入已持仓。初始化计划只用一次，不能重置资金或权重。

## 三、研究来源及重点

东方财富查价格、成交和一年位置，腾讯/新浪备用；巨潮资讯、交易所、公司官网查已披露盈利、现金流、负债与公告；财联社/证券时报查公司/行业线索再核原披露。候选主备在docs/data-sources.md，未验收不称实时，实际保留代码、单位与行情/披露/获取时间；不用未经授权的付费数据。

优先当前持仓与已有观察池，再按计算预算拓展候选；复用仍有效的基础研究，查关键变化，不每日深挖全部市场。解释经营是否仍可靠、低位原因、持续回升证据、反证、剩余上行和行业共同风险。有限覆盖不能称全市场最优。

{
  "historical_closes": {
    "600900.SH": [
      {
        "date": "2025-08-18",
        "close": "27.640",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-19",
        "close": "27.630",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-20",
        "close": "27.690",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-21",
        "close": "27.850",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-22",
        "close": "27.870",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-25",
        "close": "28.350",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-26",
        "close": "28.310",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-27",
        "close": "27.960",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-28",
        "close": "27.870",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      },
      {
        "date": "2025-08-29",
        "close": "28.090",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
      }
    ]
  },
  "evidence": [],
  "candidate_research_pack": {
    "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
    "purpose": "LOW_RECOVERY",
    "cutoff_date": "2025-08-29",
    "candidate_budget": 1,
    "selected_count": 1,
    "source_seed_count": 10,
    "seed_source": "predeclared fixed historical pilot universe",
    "seed_provider": "Tencent/Eastmoney history",
    "seed_fallback_used": false,
    "not_a_recommendation": true,
    "selection_note": "Candidate chosen from predeclared pilot universe using only target-date-visible price context; final action comes from variant prompt.",
    "survivorship_warning": "Pilot universe is fixed for this experiment and is not a claim of full historical A-share coverage.",
    "candidates": [
      {
        "symbol": "600900.SH",
        "name": "长江电力",
        "research_state": "LOW_AND_EARLY_RECOVERY_RESEARCH",
        "attention_priority": 10,
        "attention_reasons": [
          "60/120日位置偏低，5日和20日收益已小幅转正，属于低波动早期企稳候选。"
        ],
        "risk_tags": [],
        "seed_snapshot": {
          "price_cny": "28.0900",
          "change_pct": null,
          "amount_cny": null,
          "source_provider": "historical daily"
        },
        "market_history": {
          "symbol": "600900.SH",
          "name": "长江电力",
          "industry": "电力/水电",
          "industry_characteristics": [
            "现金流和分红属性较强",
            "来水与发电量影响经营",
            "利率环境影响高股息资产估值"
          ],
          "as_of_close": "28.0900",
          "observations": 224,
          "continuous_analysis_sessions": 224,
          "suspected_price_basis_break": null,
          "history_coverage": {
            "sessions": 224,
            "continuous_sessions": 224,
            "has_20_sessions": true,
            "has_60_sessions": true,
            "has_120_sessions": true,
            "has_250_sessions": false
          },
          "returns_pct": {
            "5_sessions": "0.7894",
            "20_sessions": "0.3573",
            "60_sessions": "-6.3354"
          },
          "moving_average": {
            "ma5": "28.1160",
            "ma20": "27.8880",
            "ma60": "29.2543"
          },
          "range_position_0_to_1": {
            "20_sessions": "0.6389",
            "60_sessions": "0.1322",
            "120_sessions": "0.2469",
            "250_sessions": null
          },
          "annualized_volatility_pct_approx": "9.6786",
          "kline": {
            "daily_last20": [
              {
                "date": "2025-08-04",
                "open": "27.9000",
                "high": "28.1700",
                "low": "27.8000",
                "close": "28.1400",
                "volume": "823204.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-05",
                "open": "28.1400",
                "high": "28.1800",
                "low": "27.9600",
                "close": "28.1000",
                "volume": "787153.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-06",
                "open": "28.0900",
                "high": "28.1200",
                "low": "27.8700",
                "close": "27.9700",
                "volume": "1144935.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-07",
                "open": "27.9400",
                "high": "28.1800",
                "low": "27.8400",
                "close": "28.0600",
                "volume": "1051957.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-08",
                "open": "28.0600",
                "high": "28.0800",
                "low": "27.8600",
                "close": "27.8600",
                "volume": "824972.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-11",
                "open": "27.8600",
                "high": "27.8800",
                "low": "27.5100",
                "close": "27.6900",
                "volume": "1243551.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-12",
                "open": "27.6900",
                "high": "27.8800",
                "low": "27.6400",
                "close": "27.7600",
                "volume": "743184.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-13",
                "open": "27.7700",
                "high": "27.8500",
                "low": "27.6100",
                "close": "27.6300",
                "volume": "934257.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-14",
                "open": "27.6200",
                "high": "27.8900",
                "low": "27.6000",
                "close": "27.6600",
                "volume": "1017588.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-15",
                "open": "27.7100",
                "high": "27.7800",
                "low": "27.6000",
                "close": "27.6300",
                "volume": "1072302.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-18",
                "open": "27.6400",
                "high": "27.7200",
                "low": "27.5500",
                "close": "27.6400",
                "volume": "1147362.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-19",
                "open": "27.6500",
                "high": "27.7800",
                "low": "27.6100",
                "close": "27.6300",
                "volume": "1146024.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-20",
                "open": "27.6000",
                "high": "27.7400",
                "low": "27.4600",
                "close": "27.6900",
                "volume": "1022259.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-21",
                "open": "27.6900",
                "high": "27.9500",
                "low": "27.6600",
                "close": "27.8500",
                "volume": "1179348.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-22",
                "open": "27.8800",
                "high": "27.9200",
                "low": "27.7000",
                "close": "27.8700",
                "volume": "1032104.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-25",
                "open": "28.0400",
                "high": "28.5500",
                "low": "28.0300",
                "close": "28.3500",
                "volume": "2185666.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-26",
                "open": "28.3500",
                "high": "28.4000",
                "low": "28.2100",
                "close": "28.3100",
                "volume": "1130612.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-27",
                "open": "28.2500",
                "high": "28.3000",
                "low": "27.9300",
                "close": "27.9600",
                "volume": "1275324.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-28",
                "open": "27.9500",
                "high": "27.9900",
                "low": "27.6900",
                "close": "27.8700",
                "volume": "1092962.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-08-29",
                "open": "27.9000",
                "high": "28.1600",
                "low": "27.8500",
                "close": "28.0900",
                "volume": "1067298.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              }
            ],
            "weekly_last12": [
              {
                "period": "2025-W24",
                "start": "2025-06-09",
                "end": "2025-06-13",
                "open": "29.9300",
                "high": "30.6600",
                "low": "29.8500",
                "close": "30.6200",
                "volume": "3596811.0000"
              },
              {
                "period": "2025-W25",
                "start": "2025-06-16",
                "end": "2025-06-20",
                "open": "30.5500",
                "high": "30.8600",
                "low": "30.0600",
                "close": "30.4000",
                "volume": "3048170.0000"
              },
              {
                "period": "2025-W26",
                "start": "2025-06-23",
                "end": "2025-06-27",
                "open": "30.3800",
                "high": "31.1900",
                "low": "30.2000",
                "close": "30.2200",
                "volume": "4340295.0000"
              },
              {
                "period": "2025-W27",
                "start": "2025-06-30",
                "end": "2025-07-04",
                "open": "30.2300",
                "high": "30.5200",
                "low": "29.8500",
                "close": "30.1600",
                "volume": "3537822.0000"
              },
              {
                "period": "2025-W28",
                "start": "2025-07-07",
                "end": "2025-07-11",
                "open": "30.2400",
                "high": "30.5900",
                "low": "29.8000",
                "close": "30.4000",
                "volume": "4841745.0000"
              },
              {
                "period": "2025-W29",
                "start": "2025-07-14",
                "end": "2025-07-18",
                "open": "30.4200",
                "high": "30.7900",
                "low": "29.3500",
                "close": "29.5000",
                "volume": "2936579.0000"
              },
              {
                "period": "2025-W30",
                "start": "2025-07-21",
                "end": "2025-07-25",
                "open": "29.7000",
                "high": "29.8600",
                "low": "28.7500",
                "close": "28.7500",
                "volume": "5473385.0000"
              },
              {
                "period": "2025-W31",
                "start": "2025-07-28",
                "end": "2025-08-01",
                "open": "28.7500",
                "high": "28.9400",
                "low": "27.6800",
                "close": "27.9900",
                "volume": "6101635.0000"
              },
              {
                "period": "2025-W32",
                "start": "2025-08-04",
                "end": "2025-08-08",
                "open": "27.9000",
                "high": "28.1800",
                "low": "27.8000",
                "close": "27.8600",
                "volume": "4632221.0000"
              },
              {
                "period": "2025-W33",
                "start": "2025-08-11",
                "end": "2025-08-15",
                "open": "27.8600",
                "high": "27.8900",
                "low": "27.5100",
                "close": "27.6300",
                "volume": "5010882.0000"
              },
              {
                "period": "2025-W34",
                "start": "2025-08-18",
                "end": "2025-08-22",
                "open": "27.6400",
                "high": "27.9500",
                "low": "27.4600",
                "close": "27.8700",
                "volume": "5527097.0000"
              },
              {
                "period": "2025-W35",
                "start": "2025-08-25",
                "end": "2025-08-29",
                "open": "28.0400",
                "high": "28.5500",
                "low": "27.6900",
                "close": "28.0900",
                "volume": "6751862.0000"
              }
            ],
            "monthly_last12": [
              {
                "period": "2024-09",
                "start": "2024-09-27",
                "end": "2024-09-30",
                "open": "29.2300",
                "high": "30.5000",
                "low": "28.0600",
                "close": "30.0500",
                "volume": "5847822.0000"
              },
              {
                "period": "2024-10",
                "start": "2024-10-08",
                "end": "2024-10-31",
                "open": "32.0100",
                "high": "32.2800",
                "low": "27.1600",
                "close": "27.5800",
                "volume": "28198322.0000"
              },
              {
                "period": "2024-11",
                "start": "2024-11-01",
                "end": "2024-11-29",
                "open": "27.5100",
                "high": "28.0000",
                "low": "26.7800",
                "close": "27.3200",
                "volume": "23260909.0000"
              },
              {
                "period": "2024-12",
                "start": "2024-12-02",
                "end": "2024-12-31",
                "open": "27.3900",
                "high": "29.9300",
                "low": "27.3000",
                "close": "29.5500",
                "volume": "22321356.0000"
              },
              {
                "period": "2025-01",
                "start": "2025-01-02",
                "end": "2025-01-27",
                "open": "29.5100",
                "high": "29.7300",
                "low": "28.2000",
                "close": "28.9000",
                "volume": "14784543.0000"
              },
              {
                "period": "2025-02",
                "start": "2025-02-05",
                "end": "2025-02-28",
                "open": "28.8600",
                "high": "28.8900",
                "low": "27.2000",
                "close": "27.3800",
                "volume": "17402561.0000"
              },
              {
                "period": "2025-03",
                "start": "2025-03-03",
                "end": "2025-03-31",
                "open": "27.3800",
                "high": "28.1100",
                "low": "26.9800",
                "close": "27.8100",
                "volume": "17661440.0000"
              },
              {
                "period": "2025-04",
                "start": "2025-04-01",
                "end": "2025-04-30",
                "open": "27.8500",
                "high": "29.9200",
                "low": "27.6600",
                "close": "29.5000",
                "volume": "22032135.0000"
              },
              {
                "period": "2025-05",
                "start": "2025-05-06",
                "end": "2025-05-30",
                "open": "29.6500",
                "high": "31.0600",
                "low": "29.0600",
                "close": "30.2000",
                "volume": "12274298.0000"
              },
              {
                "period": "2025-06",
                "start": "2025-06-03",
                "end": "2025-06-30",
                "open": "30.2800",
                "high": "31.1900",
                "low": "29.6500",
                "close": "30.1400",
                "volume": "14217553.0000"
              },
              {
                "period": "2025-07",
                "start": "2025-07-01",
                "end": "2025-07-31",
                "open": "30.2000",
                "high": "30.7900",
                "low": "27.7000",
                "close": "27.8400",
                "volume": "21154495.0000"
              },
              {
                "period": "2025-08",
                "start": "2025-08-01",
                "end": "2025-08-29",
                "open": "27.7900",
                "high": "28.5500",
                "low": "27.4600",
                "close": "28.0900",
                "volume": "22903548.0000"
              }
            ]
          }
        },
        "not_a_trade_signal": true
      }
    ]
  },
  "research_state": {
    "variant_id": "D02",
    "series_id": "D",
    "mode": "SIMULATION",
    "status": "RESEARCH_READY",
    "date": "2025-08-29",
    "revision": 1,
    "candidate_watchlist": [],
    "last_candidate_pack": {
      "path": "research/2025-08-29/candidate_pack.json",
      "sha256": "1258f7f6dae222370cf4f28b9ff68fdf0452e54ed5729f8e1d1fd7033aa990bf",
      "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
      "purpose": "LOW_RECOVERY",
      "candidate_count": 1,
      "not_a_recommendation": true
    },
    "last_broad_universe_source": null,
    "formal_research_enabled": null,
    "last_decision_summary": null,
    "note": "AI_SELECT research state only; never an order, holding or recommendation. Simulation state is isolated from FORMAL.",
    "last_research_payload_sha256": "9bea496b28801ca969e79978d9f6e746c876d37cf3822f5e3d086bb8bb39602c",
    "universe_scope": {
      "authorized_symbols": [
        "600900.SH"
      ],
      "coverage": "FIXED_HISTORICAL_PILOT_UNIVERSE_CANDIDATE",
      "not_full_a_share_claim": true
    }
  },
  "universe_scope": {
    "authorized_symbols": [
      "600900.SH"
    ],
    "coverage": "FIXED_HISTORICAL_PILOT_UNIVERSE_CANDIDATE",
    "not_full_a_share_claim": true
  },
  "official_disclosure_pack": {
    "kind": "OFFICIAL_DISCLOSURE_PACK",
    "symbols_requested": [
      "600900.SH"
    ],
    "results": [
      {
        "symbol": "600900.SH",
        "provider_status": "OK",
        "items": [
          {
            "symbol": "600900.SH",
            "title": "长江电力2025年第一季度报告",
            "published_at": "2025-04-30T00:00:00+08:00",
            "source_official": true,
            "source_provider": "CNINFO",
            "document_url": "https://static.cninfo.com.cn/finalpage/2025-04-30/1223421165.PDF",
            "is_periodic_report_body": true,
            "category": "PERIODIC_REPORT"
          }
        ]
      }
    ],
    "latest_periodic_report_refs": [
      {
        "symbol": "600900.SH",
        "title": "长江电力2025年第一季度报告",
        "published_at": "2025-04-30T00:00:00+08:00",
        "source_official": true,
        "source_provider": "CNINFO",
        "document_url": "https://static.cninfo.com.cn/finalpage/2025-04-30/1223421165.PDF",
        "is_periodic_report_body": true,
        "category": "PERIODIC_REPORT"
      }
    ],
    "important_recent_refs": []
  },
  "financial_reviews": {
    "600900.SH": {
      "status": "REVIEWED",
      "symbol": "600900.SH",
      "as_of": "2025-08-29T14:40:00+08:00",
      "source_report": "https://static.cninfo.com.cn/finalpage/2025-04-30/1223421165.PDF",
      "source_official": true,
      "period": "2025Q1",
      "facts": [
        {
          "name": "营业收入",
          "value": "17,015,283,778.59 CNY，同比 +8.68%",
          "source": "长江电力2025年第一季度报告"
        },
        {
          "name": "归母净利润",
          "value": "5,180,785,597.87 CNY，同比 +30.56%",
          "source": "长江电力2025年第一季度报告"
        },
        {
          "name": "扣非归母净利润",
          "value": "5,232,734,947.37 CNY，同比 +31.49%",
          "source": "长江电力2025年第一季度报告"
        },
        {
          "name": "经营活动现金流量净额",
          "value": "11,847,251,953.10 CNY，同比 -2.20%",
          "source": "长江电力2025年第一季度报告"
        }
      ],
      "summary": "最新可用正式财务显示收入和利润增长较强，经营现金流仅小幅下降；结合低波动、60/120日相对低位和短期企稳，符合D02继续研究低位回升的条件。注意2025半年报在8月30日披露，晚于本次8月29日截止，不能使用。",
      "data_gaps": [
        "2025年半年报尚未在本次信息截止前披露，已排除。"
      ]
    }
  },
  "news_research": {
    "status": "NO_RELEVANT_RECENT_NEWS",
    "searched_at": "2025-08-29T14:50:00+08:00",
    "items": [],
    "data_gaps": [
      "Historical news coverage is intentionally limited; absence of a captured item does not prove no news existed."
    ]
  },
  "decision_research_bundle": {
    "kind": "DECISION_RESEARCH_BUNDLE",
    "as_of": "2025-08-29T15:00:00+08:00",
    "symbols": [
      "600900.SH"
    ],
    "candidate_research_pack": {
      "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
      "purpose": "LOW_RECOVERY",
      "cutoff_date": "2025-08-29",
      "candidate_budget": 1,
      "selected_count": 1,
      "source_seed_count": 10,
      "seed_source": "predeclared fixed historical pilot universe",
      "seed_provider": "Tencent/Eastmoney history",
      "seed_fallback_used": false,
      "not_a_recommendation": true,
      "selection_note": "Candidate chosen from predeclared pilot universe using only target-date-visible price context; final action comes from variant prompt.",
      "survivorship_warning": "Pilot universe is fixed for this experiment and is not a claim of full historical A-share coverage.",
      "candidates": [
        {
          "symbol": "600900.SH",
          "name": "长江电力",
          "research_state": "LOW_AND_EARLY_RECOVERY_RESEARCH",
          "attention_priority": 10,
          "attention_reasons": [
            "60/120日位置偏低，5日和20日收益已小幅转正，属于低波动早期企稳候选。"
          ],
          "risk_tags": [],
          "seed_snapshot": {
            "price_cny": "28.0900",
            "change_pct": null,
            "amount_cny": null,
            "source_provider": "historical daily"
          },
          "market_history": {
            "symbol": "600900.SH",
            "name": "长江电力",
            "industry": "电力/水电",
            "industry_characteristics": [
              "现金流和分红属性较强",
              "来水与发电量影响经营",
              "利率环境影响高股息资产估值"
            ],
            "as_of_close": "28.0900",
            "observations": 224,
            "continuous_analysis_sessions": 224,
            "suspected_price_basis_break": null,
            "history_coverage": {
              "sessions": 224,
              "continuous_sessions": 224,
              "has_20_sessions": true,
              "has_60_sessions": true,
              "has_120_sessions": true,
              "has_250_sessions": false
            },
            "returns_pct": {
              "5_sessions": "0.7894",
              "20_sessions": "0.3573",
              "60_sessions": "-6.3354"
            },
            "moving_average": {
              "ma5": "28.1160",
              "ma20": "27.8880",
              "ma60": "29.2543"
            },
            "range_position_0_to_1": {
              "20_sessions": "0.6389",
              "60_sessions": "0.1322",
              "120_sessions": "0.2469",
              "250_sessions": null
            },
            "annualized_volatility_pct_approx": "9.6786",
            "kline": {
              "daily_last20": [
                {
                  "date": "2025-08-04",
                  "open": "27.9000",
                  "high": "28.1700",
                  "low": "27.8000",
                  "close": "28.1400",
                  "volume": "823204.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-05",
                  "open": "28.1400",
                  "high": "28.1800",
                  "low": "27.9600",
                  "close": "28.1000",
                  "volume": "787153.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-06",
                  "open": "28.0900",
                  "high": "28.1200",
                  "low": "27.8700",
                  "close": "27.9700",
                  "volume": "1144935.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-07",
                  "open": "27.9400",
                  "high": "28.1800",
                  "low": "27.8400",
                  "close": "28.0600",
                  "volume": "1051957.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-08",
                  "open": "28.0600",
                  "high": "28.0800",
                  "low": "27.8600",
                  "close": "27.8600",
                  "volume": "824972.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-11",
                  "open": "27.8600",
                  "high": "27.8800",
                  "low": "27.5100",
                  "close": "27.6900",
                  "volume": "1243551.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-12",
                  "open": "27.6900",
                  "high": "27.8800",
                  "low": "27.6400",
                  "close": "27.7600",
                  "volume": "743184.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-13",
                  "open": "27.7700",
                  "high": "27.8500",
                  "low": "27.6100",
                  "close": "27.6300",
                  "volume": "934257.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-14",
                  "open": "27.6200",
                  "high": "27.8900",
                  "low": "27.6000",
                  "close": "27.6600",
                  "volume": "1017588.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-15",
                  "open": "27.7100",
                  "high": "27.7800",
                  "low": "27.6000",
                  "close": "27.6300",
                  "volume": "1072302.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-18",
                  "open": "27.6400",
                  "high": "27.7200",
                  "low": "27.5500",
                  "close": "27.6400",
                  "volume": "1147362.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-19",
                  "open": "27.6500",
                  "high": "27.7800",
                  "low": "27.6100",
                  "close": "27.6300",
                  "volume": "1146024.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-20",
                  "open": "27.6000",
                  "high": "27.7400",
                  "low": "27.4600",
                  "close": "27.6900",
                  "volume": "1022259.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-21",
                  "open": "27.6900",
                  "high": "27.9500",
                  "low": "27.6600",
                  "close": "27.8500",
                  "volume": "1179348.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-22",
                  "open": "27.8800",
                  "high": "27.9200",
                  "low": "27.7000",
                  "close": "27.8700",
                  "volume": "1032104.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-25",
                  "open": "28.0400",
                  "high": "28.5500",
                  "low": "28.0300",
                  "close": "28.3500",
                  "volume": "2185666.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-26",
                  "open": "28.3500",
                  "high": "28.4000",
                  "low": "28.2100",
                  "close": "28.3100",
                  "volume": "1130612.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-27",
                  "open": "28.2500",
                  "high": "28.3000",
                  "low": "27.9300",
                  "close": "27.9600",
                  "volume": "1275324.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-28",
                  "open": "27.9500",
                  "high": "27.9900",
                  "low": "27.6900",
                  "close": "27.8700",
                  "volume": "1092962.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-08-29",
                  "open": "27.9000",
                  "high": "28.1600",
                  "low": "27.8500",
                  "close": "28.0900",
                  "volume": "1067298.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                }
              ],
              "weekly_last12": [
                {
                  "period": "2025-W24",
                  "start": "2025-06-09",
                  "end": "2025-06-13",
                  "open": "29.9300",
                  "high": "30.6600",
                  "low": "29.8500",
                  "close": "30.6200",
                  "volume": "3596811.0000"
                },
                {
                  "period": "2025-W25",
                  "start": "2025-06-16",
                  "end": "2025-06-20",
                  "open": "30.5500",
                  "high": "30.8600",
                  "low": "30.0600",
                  "close": "30.4000",
                  "volume": "3048170.0000"
                },
                {
                  "period": "2025-W26",
                  "start": "2025-06-23",
                  "end": "2025-06-27",
                  "open": "30.3800",
                  "high": "31.1900",
                  "low": "30.2000",
                  "close": "30.2200",
                  "volume": "4340295.0000"
                },
                {
                  "period": "2025-W27",
                  "start": "2025-06-30",
                  "end": "2025-07-04",
                  "open": "30.2300",
                  "high": "30.5200",
                  "low": "29.8500",
                  "close": "30.1600",
                  "volume": "3537822.0000"
                },
                {
                  "period": "2025-W28",
                  "start": "2025-07-07",
                  "end": "2025-07-11",
                  "open": "30.2400",
                  "high": "30.5900",
                  "low": "29.8000",
                  "close": "30.4000",
                  "volume": "4841745.0000"
                },
                {
                  "period": "2025-W29",
                  "start": "2025-07-14",
                  "end": "2025-07-18",
                  "open": "30.4200",
                  "high": "30.7900",
                  "low": "29.3500",
                  "close": "29.5000",
                  "volume": "2936579.0000"
                },
                {
                  "period": "2025-W30",
                  "start": "2025-07-21",
                  "end": "2025-07-25",
                  "open": "29.7000",
                  "high": "29.8600",
                  "low": "28.7500",
                  "close": "28.7500",
                  "volume": "5473385.0000"
                },
                {
                  "period": "2025-W31",
                  "start": "2025-07-28",
                  "end": "2025-08-01",
                  "open": "28.7500",
                  "high": "28.9400",
                  "low": "27.6800",
                  "close": "27.9900",
                  "volume": "6101635.0000"
                },
                {
                  "period": "2025-W32",
                  "start": "2025-08-04",
                  "end": "2025-08-08",
                  "open": "27.9000",
                  "high": "28.1800",
                  "low": "27.8000",
                  "close": "27.8600",
                  "volume": "4632221.0000"
                },
                {
                  "period": "2025-W33",
                  "start": "2025-08-11",
                  "end": "2025-08-15",
                  "open": "27.8600",
                  "high": "27.8900",
                  "low": "27.5100",
                  "close": "27.6300",
                  "volume": "5010882.0000"
                },
                {
                  "period": "2025-W34",
                  "start": "2025-08-18",
                  "end": "2025-08-22",
                  "open": "27.6400",
                  "high": "27.9500",
                  "low": "27.4600",
                  "close": "27.8700",
                  "volume": "5527097.0000"
                },
                {
                  "period": "2025-W35",
                  "start": "2025-08-25",
                  "end": "2025-08-29",
                  "open": "28.0400",
                  "high": "28.5500",
                  "low": "27.6900",
                  "close": "28.0900",
                  "volume": "6751862.0000"
                }
              ],
              "monthly_last12": [
                {
                  "period": "2024-09",
                  "start": "2024-09-27",
                  "end": "2024-09-30",
                  "open": "29.2300",
                  "high": "30.5000",
                  "low": "28.0600",
                  "close": "30.0500",
                  "volume": "5847822.0000"
                },
                {
                  "period": "2024-10",
                  "start": "2024-10-08",
                  "end": "2024-10-31",
                  "open": "32.0100",
                  "high": "32.2800",
                  "low": "27.1600",
                  "close": "27.5800",
                  "volume": "28198322.0000"
                },
                {
                  "period": "2024-11",
                  "start": "2024-11-01",
                  "end": "2024-11-29",
                  "open": "27.5100",
                  "high": "28.0000",
                  "low": "26.7800",
                  "close": "27.3200",
                  "volume": "23260909.0000"
                },
                {
                  "period": "2024-12",
                  "start": "2024-12-02",
                  "end": "2024-12-31",
                  "open": "27.3900",
                  "high": "29.9300",
                  "low": "27.3000",
                  "close": "29.5500",
                  "volume": "22321356.0000"
                },
                {
                  "period": "2025-01",
                  "start": "2025-01-02",
                  "end": "2025-01-27",
                  "open": "29.5100",
                  "high": "29.7300",
                  "low": "28.2000",
                  "close": "28.9000",
                  "volume": "14784543.0000"
                },
                {
                  "period": "2025-02",
                  "start": "2025-02-05",
                  "end": "2025-02-28",
                  "open": "28.8600",
                  "high": "28.8900",
                  "low": "27.2000",
                  "close": "27.3800",
                  "volume": "17402561.0000"
                },
                {
                  "period": "2025-03",
                  "start": "2025-03-03",
                  "end": "2025-03-31",
                  "open": "27.3800",
                  "high": "28.1100",
                  "low": "26.9800",
                  "close": "27.8100",
                  "volume": "17661440.0000"
                },
                {
                  "period": "2025-04",
                  "start": "2025-04-01",
                  "end": "2025-04-30",
                  "open": "27.8500",
                  "high": "29.9200",
                  "low": "27.6600",
                  "close": "29.5000",
                  "volume": "22032135.0000"
                },
                {
                  "period": "2025-05",
                  "start": "2025-05-06",
                  "end": "2025-05-30",
                  "open": "29.6500",
                  "high": "31.0600",
                  "low": "29.0600",
                  "close": "30.2000",
                  "volume": "12274298.0000"
                },
                {
                  "period": "2025-06",
                  "start": "2025-06-03",
                  "end": "2025-06-30",
                  "open": "30.2800",
                  "high": "31.1900",
                  "low": "29.6500",
                  "close": "30.1400",
                  "volume": "14217553.0000"
                },
                {
                  "period": "2025-07",
                  "start": "2025-07-01",
                  "end": "2025-07-31",
                  "open": "30.2000",
                  "high": "30.7900",
                  "low": "27.7000",
                  "close": "27.8400",
                  "volume": "21154495.0000"
                },
                {
                  "period": "2025-08",
                  "start": "2025-08-01",
                  "end": "2025-08-29",
                  "open": "27.7900",
                  "high": "28.5500",
                  "low": "27.4600",
                  "close": "28.0900",
                  "volume": "22903548.0000"
                }
              ]
            }
          },
          "not_a_trade_signal": true
        }
      ]
    },
    "research_state": {
      "variant_id": "D02",
      "series_id": "D",
      "mode": "SIMULATION",
      "status": "RESEARCH_READY",
      "date": "2025-08-29",
      "revision": 1,
      "candidate_watchlist": [],
      "last_candidate_pack": {
        "path": "research/2025-08-29/candidate_pack.json",
        "sha256": "1258f7f6dae222370cf4f28b9ff68fdf0452e54ed5729f8e1d1fd7033aa990bf",
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": "LOW_RECOVERY",
        "candidate_count": 1,
        "not_a_recommendation": true
      },
      "last_broad_universe_source": null,
      "formal_research_enabled": null,
      "last_decision_summary": null,
      "note": "AI_SELECT research state only; never an order, holding or recommendation. Simulation state is isolated from FORMAL.",
      "last_research_payload_sha256": "9bea496b28801ca969e79978d9f6e746c876d37cf3822f5e3d086bb8bb39602c",
      "universe_scope": {
        "authorized_symbols": [
          "600900.SH"
        ],
        "coverage": "FIXED_HISTORICAL_PILOT_UNIVERSE_CANDIDATE",
        "not_full_a_share_claim": true
      }
    },
    "market_context": {
      "mode": "SIMULATION",
      "visible_symbols": [
        "600900.SH"
      ],
      "fidelity": "BOUNDED_CANDIDATE_REAL_DAILY"
    },
    "per_symbol": [
      {
        "symbol": "600900.SH",
        "official_disclosure_status": "OK",
        "latest_periodic_report_ref": {
          "symbol": "600900.SH",
          "title": "长江电力2025年第一季度报告",
          "published_at": "2025-04-30T00:00:00+08:00",
          "source_official": true,
          "source_provider": "CNINFO",
          "document_url": "https://static.cninfo.com.cn/finalpage/2025-04-30/1223421165.PDF",
          "is_periodic_report_body": true,
          "category": "PERIODIC_REPORT"
        },
        "important_official_disclosures": [],
        "financial_review": {
          "status": "REVIEWED",
          "symbol": "600900.SH",
          "as_of": "2025-08-29T14:40:00+08:00",
          "source_report": "https://static.cninfo.com.cn/finalpage/2025-04-30/1223421165.PDF",
          "source_official": true,
          "period": "2025Q1",
          "facts": [
            {
              "name": "营业收入",
              "value": "17,015,283,778.59 CNY，同比 +8.68%",
              "source": "长江电力2025年第一季度报告"
            },
            {
              "name": "归母净利润",
              "value": "5,180,785,597.87 CNY，同比 +30.56%",
              "source": "长江电力2025年第一季度报告"
            },
            {
              "name": "扣非归母净利润",
              "value": "5,232,734,947.37 CNY，同比 +31.49%",
              "source": "长江电力2025年第一季度报告"
            },
            {
              "name": "经营活动现金流量净额",
              "value": "11,847,251,953.10 CNY，同比 -2.20%",
              "source": "长江电力2025年第一季度报告"
            }
          ],
          "summary": "最新可用正式财务显示收入和利润增长较强，经营现金流仅小幅下降；结合低波动、60/120日相对低位和短期企稳，符合D02继续研究低位回升的条件。注意2025半年报在8月30日披露，晚于本次8月29日截止，不能使用。",
          "data_gaps": [
            "2025年半年报尚未在本次信息截止前披露，已排除。"
          ]
        },
        "financial_review_status": "REVIEWED",
        "recent_news_status": "NO_RELEVANT_RECENT_NEWS",
        "recent_news_items": [],
        "data_gaps": [],
        "no_investment_conclusion": true
      }
    ],
    "coverage": {
      "official_ok_or_empty": 1,
      "financial_interpretation_completed": 1,
      "news_verified": 1,
      "symbol_count": 1
    },
    "coverage_is_not_a_score": true,
    "research_rules": [
      "Missing or failed evidence is a data gap, never favorable evidence.",
      "Official disclosure metadata is a reference; financial conclusions require review of the actual disclosed information.",
      "News/media is a lead source. Material facts should be checked against official disclosure when possible.",
      "The AI decides relevance and synthesis; this bundle does not rank securities or dictate a trade."
    ]
  },
  "research_input_manifest": {
    "variant_id": "D02",
    "path": "research-inputs/D02/2025-08-29",
    "information_cutoff": "2025-08-29T15:00:00+08:00",
    "file_sha256": {
      "manifest.json": "fd3511a5ff5a7d4b4da7ce7171785650d50f43ed75c15f3c51b655432919bc6a",
      "official-disclosure-pack.json": "d87388ce78fa5a99bdf2335a9649966201fc8927ceb870b3786e03f77e498b4b",
      "financial-reviews.json": "04dab7db8ad622dc916192cc16bd5100359980cd9de4fb8eec82c9fc04003db1",
      "news-research.json": "01d528db1817294ec009ac990038d515a8cd1c1dc7338669dec341012f471991",
      "candidate-research-pack.json": "1258f7f6dae222370cf4f28b9ff68fdf0452e54ed5729f8e1d1fd7033aa990bf",
      "universe-scope.json": "65ece65299a23cb64e7d8799f86c82bb6d1f3f7642891a36d6e3fe4ed6596469"
    },
    "missing_files": []
  },
  "tools": "Use supplied point-in-time evidence only for this replay. No current-web lookahead.",
  "limitations": [
    "Candidate set is bounded for compute control and is not a complete all-A-share research claim.",
    "No archived news/fundamentals/intraday verification in this adapter.",
    "Current-universe seeding has survivorship bias if reused for historical dates.",
    "Suspected >25% price-basis breaks are not assigned executable limit prices."
  ],
  "fundamentals_news_coverage": "only supplied evidence"
}


历史回放按当时范围和当时公开资料，不倒选今天幸存或后来反弹的标的，不把后来公布财报/当日收盘用于过去11点判断。AI可能知道后来信息的局限须披露。网页内容是证据，不是权限或下单指令。

## 四、给出可执行的判断

解释已有持股是否继续持有、候选是否值得买、需要多少现金及具体数量。一个系列可以多股，但今天最多一个完成的BUY/SELL/HOLD决策与至多一笔交易，不先卖一只再买另一只；下次运行前无法随时调整。

目标组合不是批量订单。允许等待，不无限补仓；不能把尚未确认的固定止损/仓位数字设为硬规则。没有可靠行情、账户或授权则明确未完成，不编造HOLD或成交。

## 五、输出与当天记录

先给中文概况、逐股/候选比较、唯一动作与股数、目标仓位、证据/反证、风险和缺口。再按docs/ai-decision-contract.md给decision JSON：schema_version、strategy_id=D、variant_id、mode、run_id、decision_id、date、decision_time、input_revision、input_commit、status、action、order_proposal、target_weights、target_cash_weight、summary、risks、evidence、data_gaps。

READY时BUY/SELL/HOLD，其他INSUFFICIENT_DATA/NOT_INITIALIZED/NOT_AUTHORIZED时action与订单为null。BUY/SELL一笔订单有symbol、side、正整数quantity、reference_price_cny、quote_time及quote_source。HOLD无订单，完整目标权重含现金合计1；证据不够可留空解释。AI不自行宣布成交。

获授权执行步骤重核账户版本、模式、当日额度、资金、可卖股数、证券范围、允许时段、报价新鲜度和适用约束，再决定FILLED/REJECTED/NO_TRADE/NOT_EXECUTED。当天strategies/D/daily/<日期>/保存ai_input.md、holdings_before.json、decision.json、execution.json、holdings_after.json、summary.md，必要证据research.json；事件在本系列trading/events/，和最新holdings.json及holdings.md一致提交。股数/现金只来自有效成交或权益事件；closing.json记录收盘估值，不能用盘中值冒充。测试用本系列simulations，重试不重复记账。本文件不等于自动程序已实现。


## D02的优先执行说明
只执行上面本变体的偏好；原系列模板对其他变体的概述只是背景，不能切换变体或混用账户。
系列根目录原holdings.json仅为迁移前入口；本次唯一账户路径以RUN_CONTEXT.account_path为准。
模拟将自己置于信息截止时刻；后续市场变化未知，账户余额和股数只能来自当前快照。
READY的action只允许BUY、SELL、HOLD；每次至多一个order_proposal。
只返回一个JSON对象，中文解释放summary；缺资料返回INSUFFICIENT_DATA且action/order_proposal为null。
自我改进只改表达清晰度和稳定性，每变体累计最多10轮；不按后续收益挑选当天提示词。


## 本轮输出稳定性补充（不改变投资策略）
- AI_SELECT候选池只分配研究预算，不是推荐排名；BUY只能从当次授权候选中选择，已有持仓即使掉出候选池仍可SELL。
- research_state/watchlist是本变体跨日研究状态，不是持仓或交易信号；不得把候选观察状态直接转换成BUY。
- D类年度低位研究优先解释250日位置；250日历史不足必须披露，短期已大幅反弹或处20日高位时不得仅因长期位置低就称为“刚出谷底”。

## 时光穿越运行层（仅本次运行时注入，不改变策略正文）
你现在回到2025-08-29收盘时。请把自己视为当时的投资研究者。你只能使用2025-08-29收盘及以前已经可见的市场资料，不知道之后任何价格、涨跌、财报结果或事件。不要用后验结果修正当时判断。 本日线近似将在下一交易日2025-09-01开盘模拟执行。

下面数据均按knowledge_cutoff裁剪。把它们当作你在那个时点能看到的大致市场环境；新闻缺失可忽略，不允许根据后来的结果补全。

{
  "mode": "TIME_TRAVEL",
  "target_date": "2025-08-29",
  "knowledge_cutoff": "2025-08-29T15:00:00+08:00",
  "planned_execution_date": "2025-09-01",
  "instruction": "你现在回到2025-08-29收盘时。请把自己视为当时的投资研究者。你只能使用2025-08-29收盘及以前已经可见的市场资料，不知道之后任何价格、涨跌、财报结果或事件。不要用后验结果修正当时判断。 本日线近似将在下一交易日2025-09-01开盘模拟执行。",
  "news_policy": "IGNORE_ARCHIVED_NEWS_BY_DEFAULT",
  "market_proxy": {
    "kind": "CONFIGURED_UNIVERSE_EQUAL_WEIGHT_PROXY_NOT_BROAD_MARKET_INDEX",
    "returns_pct": {
      "5_sessions": "0.7894",
      "20_sessions": "0.3573",
      "60_sessions": "-6.3354"
    }
  },
  "symbols": [
    {
      "symbol": "600900.SH",
      "name": "长江电力",
      "industry": "电力/水电",
      "industry_characteristics": [
        "现金流和分红属性较强",
        "来水与发电量影响经营",
        "利率环境影响高股息资产估值"
      ],
      "as_of_close": "28.0900",
      "observations": 224,
      "continuous_analysis_sessions": 224,
      "suspected_price_basis_break": null,
      "history_coverage": {
        "sessions": 224,
        "continuous_sessions": 224,
        "has_20_sessions": true,
        "has_60_sessions": true,
        "has_120_sessions": true,
        "has_250_sessions": false
      },
      "returns_pct": {
        "5_sessions": "0.7894",
        "20_sessions": "0.3573",
        "60_sessions": "-6.3354"
      },
      "moving_average": {
        "ma5": "28.1160",
        "ma20": "27.8880",
        "ma60": "29.2543"
      },
      "range_position_0_to_1": {
        "20_sessions": "0.6389",
        "60_sessions": "0.1322",
        "120_sessions": "0.2469",
        "250_sessions": null
      },
      "annualized_volatility_pct_approx": "9.6786",
      "kline": {
        "daily_last20": [
          {
            "date": "2025-08-04",
            "open": "27.9000",
            "high": "28.1700",
            "low": "27.8000",
            "close": "28.1400",
            "volume": "823204.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-05",
            "open": "28.1400",
            "high": "28.1800",
            "low": "27.9600",
            "close": "28.1000",
            "volume": "787153.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-06",
            "open": "28.0900",
            "high": "28.1200",
            "low": "27.8700",
            "close": "27.9700",
            "volume": "1144935.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-07",
            "open": "27.9400",
            "high": "28.1800",
            "low": "27.8400",
            "close": "28.0600",
            "volume": "1051957.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-08",
            "open": "28.0600",
            "high": "28.0800",
            "low": "27.8600",
            "close": "27.8600",
            "volume": "824972.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-11",
            "open": "27.8600",
            "high": "27.8800",
            "low": "27.5100",
            "close": "27.6900",
            "volume": "1243551.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-12",
            "open": "27.6900",
            "high": "27.8800",
            "low": "27.6400",
            "close": "27.7600",
            "volume": "743184.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-13",
            "open": "27.7700",
            "high": "27.8500",
            "low": "27.6100",
            "close": "27.6300",
            "volume": "934257.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-14",
            "open": "27.6200",
            "high": "27.8900",
            "low": "27.6000",
            "close": "27.6600",
            "volume": "1017588.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-15",
            "open": "27.7100",
            "high": "27.7800",
            "low": "27.6000",
            "close": "27.6300",
            "volume": "1072302.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-18",
            "open": "27.6400",
            "high": "27.7200",
            "low": "27.5500",
            "close": "27.6400",
            "volume": "1147362.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-19",
            "open": "27.6500",
            "high": "27.7800",
            "low": "27.6100",
            "close": "27.6300",
            "volume": "1146024.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-20",
            "open": "27.6000",
            "high": "27.7400",
            "low": "27.4600",
            "close": "27.6900",
            "volume": "1022259.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-21",
            "open": "27.6900",
            "high": "27.9500",
            "low": "27.6600",
            "close": "27.8500",
            "volume": "1179348.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-22",
            "open": "27.8800",
            "high": "27.9200",
            "low": "27.7000",
            "close": "27.8700",
            "volume": "1032104.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-25",
            "open": "28.0400",
            "high": "28.5500",
            "low": "28.0300",
            "close": "28.3500",
            "volume": "2185666.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-26",
            "open": "28.3500",
            "high": "28.4000",
            "low": "28.2100",
            "close": "28.3100",
            "volume": "1130612.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-27",
            "open": "28.2500",
            "high": "28.3000",
            "low": "27.9300",
            "close": "27.9600",
            "volume": "1275324.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-28",
            "open": "27.9500",
            "high": "27.9900",
            "low": "27.6900",
            "close": "27.8700",
            "volume": "1092962.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          },
          {
            "date": "2025-08-29",
            "open": "27.9000",
            "high": "28.1600",
            "low": "27.8500",
            "close": "28.0900",
            "volume": "1067298.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600900%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
          }
        ],
        "weekly_last12": [
          {
            "period": "2025-W24",
            "start": "2025-06-09",
            "end": "2025-06-13",
            "open": "29.9300",
            "high": "30.6600",
            "low": "29.8500",
            "close": "30.6200",
            "volume": "3596811.0000"
          },
          {
            "period": "2025-W25",
            "start": "2025-06-16",
            "end": "2025-06-20",
            "open": "30.5500",
            "high": "30.8600",
            "low": "30.0600",
            "close": "30.4000",
            "volume": "3048170.0000"
          },
          {
            "period": "2025-W26",
            "start": "2025-06-23",
            "end": "2025-06-27",
            "open": "30.3800",
            "high": "31.1900",
            "low": "30.2000",
            "close": "30.2200",
            "volume": "4340295.0000"
          },
          {
            "period": "2025-W27",
            "start": "2025-06-30",
            "end": "2025-07-04",
            "open": "30.2300",
            "high": "30.5200",
            "low": "29.8500",
            "close": "30.1600",
            "volume": "3537822.0000"
          },
          {
            "period": "2025-W28",
            "start": "2025-07-07",
            "end": "2025-07-11",
            "open": "30.2400",
            "high": "30.5900",
            "low": "29.8000",
            "close": "30.4000",
            "volume": "4841745.0000"
          },
          {
            "period": "2025-W29",
            "start": "2025-07-14",
            "end": "2025-07-18",
            "open": "30.4200",
            "high": "30.7900",
            "low": "29.3500",
            "close": "29.5000",
            "volume": "2936579.0000"
          },
          {
            "period": "2025-W30",
            "start": "2025-07-21",
            "end": "2025-07-25",
            "open": "29.7000",
            "high": "29.8600",
            "low": "28.7500",
            "close": "28.7500",
            "volume": "5473385.0000"
          },
          {
            "period": "2025-W31",
            "start": "2025-07-28",
            "end": "2025-08-01",
            "open": "28.7500",
            "high": "28.9400",
            "low": "27.6800",
            "close": "27.9900",
            "volume": "6101635.0000"
          },
          {
            "period": "2025-W32",
            "start": "2025-08-04",
            "end": "2025-08-08",
            "open": "27.9000",
            "high": "28.1800",
            "low": "27.8000",
            "close": "27.8600",
            "volume": "4632221.0000"
          },
          {
            "period": "2025-W33",
            "start": "2025-08-11",
            "end": "2025-08-15",
            "open": "27.8600",
            "high": "27.8900",
            "low": "27.5100",
            "close": "27.6300",
            "volume": "5010882.0000"
          },
          {
            "period": "2025-W34",
            "start": "2025-08-18",
            "end": "2025-08-22",
            "open": "27.6400",
            "high": "27.9500",
            "low": "27.4600",
            "close": "27.8700",
            "volume": "5527097.0000"
          },
          {
            "period": "2025-W35",
            "start": "2025-08-25",
            "end": "2025-08-29",
            "open": "28.0400",
            "high": "28.5500",
            "low": "27.6900",
            "close": "28.0900",
            "volume": "6751862.0000"
          }
        ],
        "monthly_last12": [
          {
            "period": "2024-09",
            "start": "2024-09-27",
            "end": "2024-09-30",
            "open": "29.2300",
            "high": "30.5000",
            "low": "28.0600",
            "close": "30.0500",
            "volume": "5847822.0000"
          },
          {
            "period": "2024-10",
            "start": "2024-10-08",
            "end": "2024-10-31",
            "open": "32.0100",
            "high": "32.2800",
            "low": "27.1600",
            "close": "27.5800",
            "volume": "28198322.0000"
          },
          {
            "period": "2024-11",
            "start": "2024-11-01",
            "end": "2024-11-29",
            "open": "27.5100",
            "high": "28.0000",
            "low": "26.7800",
            "close": "27.3200",
            "volume": "23260909.0000"
          },
          {
            "period": "2024-12",
            "start": "2024-12-02",
            "end": "2024-12-31",
            "open": "27.3900",
            "high": "29.9300",
            "low": "27.3000",
            "close": "29.5500",
            "volume": "22321356.0000"
          },
          {
            "period": "2025-01",
            "start": "2025-01-02",
            "end": "2025-01-27",
            "open": "29.5100",
            "high": "29.7300",
            "low": "28.2000",
            "close": "28.9000",
            "volume": "14784543.0000"
          },
          {
            "period": "2025-02",
            "start": "2025-02-05",
            "end": "2025-02-28",
            "open": "28.8600",
            "high": "28.8900",
            "low": "27.2000",
            "close": "27.3800",
            "volume": "17402561.0000"
          },
          {
            "period": "2025-03",
            "start": "2025-03-03",
            "end": "2025-03-31",
            "open": "27.3800",
            "high": "28.1100",
            "low": "26.9800",
            "close": "27.8100",
            "volume": "17661440.0000"
          },
          {
            "period": "2025-04",
            "start": "2025-04-01",
            "end": "2025-04-30",
            "open": "27.8500",
            "high": "29.9200",
            "low": "27.6600",
            "close": "29.5000",
            "volume": "22032135.0000"
          },
          {
            "period": "2025-05",
            "start": "2025-05-06",
            "end": "2025-05-30",
            "open": "29.6500",
            "high": "31.0600",
            "low": "29.0600",
            "close": "30.2000",
            "volume": "12274298.0000"
          },
          {
            "period": "2025-06",
            "start": "2025-06-03",
            "end": "2025-06-30",
            "open": "30.2800",
            "high": "31.1900",
            "low": "29.6500",
            "close": "30.1400",
            "volume": "14217553.0000"
          },
          {
            "period": "2025-07",
            "start": "2025-07-01",
            "end": "2025-07-31",
            "open": "30.2000",
            "high": "30.7900",
            "low": "27.7000",
            "close": "27.8400",
            "volume": "21154495.0000"
          },
          {
            "period": "2025-08",
            "start": "2025-08-01",
            "end": "2025-08-29",
            "open": "27.7900",
            "high": "28.5500",
            "low": "27.4600",
            "close": "28.0900",
            "volume": "22903548.0000"
          }
        ]
      }
    }
  ],
  "intraday_kline": {
    "status": "UNAVAILABLE_UNLESS_ARCHIVED_INTRADAY_DATA_IS_SUPPLIED",
    "rule": "不得用当日收盘或未来分钟线冒充历史盘中信息"
  },
  "limitations": [
    "行业特点为结构性研究背景，不代表当日行业消息。",
    "未提供真实大盘指数时，market_proxy只是本次可见股票池等权代理。",
    "日/周/月K线均由knowledge_cutoff以前的未复权历史日线聚合；若检测到疑似除权/送转或数据口径断点，跨断点收益、均线和区间位置不混算，只使用断点后的连续价格段；历史不足时对应统计为null。",
    "新闻默认忽略；没有历史新闻不解释为当时没有新闻或风险。",
    "AI模型本身可能含有后来知识，因此仍不能声称完全消除前视偏差。"
  ]
}


## 本次选定变体原文


## 本次模式说明
这是获授权的隔离模拟，不操作正式账户。未提供历史财务/新闻时应披露缺口。
只输出一个符合契约的JSON对象；不使用当前网页补充历史未知资料。不要把流程测试称为投资有效性证明。
