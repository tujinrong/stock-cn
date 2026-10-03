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
  "run_id": "eval-continuation-def-20250530-20250530-D02",
  "decision_id": "eval-continuation-def-20250530-20250530-D02-2025-06-03",
  "date": "2025-06-03",
  "decision_time": "2025-05-30T15:00:00+08:00",
  "information_cutoff": "2025-05-30T15:00:00+08:00",
  "execution_time": "2025-06-03T09:30:00+08:00",
  "timezone": "Asia/Shanghai",
  "execution_basis": "PREVIOUS_CLOSE_NEXT_OPEN_NOT_11AM",
  "input_revision": 1,
  "input_commit": "473c2a38e37ec17e67aecf3c1be6fc1e28de5dd3",
  "input_snapshot_sha256": "eb6effe41d447feb16a6ae20c8bcc1951f877d6c17ba849e59a250ee46cdb1ad",
  "account_path": "strategies\\D\\variants\\D02\\simulations\\eval-continuation-def-20250530-20250530\\holdings.json",
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
  "date": "2025-05-30",
  "initial_capital_cny": "200000.00",
  "cash_cny": "200000.00",
  "total_equity_cny": "200000.00",
  "positions": [],
  "_meta": {
    "schema_version": "0.4",
    "mode": "SIMULATION",
    "paper_only": true,
    "variant_id": "D02",
    "test_id": "eval-continuation-def-20250530-20250530",
    "revision": 1,
    "valuation_time": "2025-05-30T15:00:00+08:00",
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
  "600309.SH"
]


未初始化时null不是0元；无持仓显示无持仓。每次传入全部实际持股，某股行情缺失仍保留该行，候选不能混入已持仓。初始化计划只用一次，不能重置资金或权重。

## 三、研究来源及重点

东方财富查价格、成交和一年位置，腾讯/新浪备用；巨潮资讯、交易所、公司官网查已披露盈利、现金流、负债与公告；财联社/证券时报查公司/行业线索再核原披露。候选主备在docs/data-sources.md，未验收不称实时，实际保留代码、单位与行情/披露/获取时间；不用未经授权的付费数据。

优先当前持仓与已有观察池，再按计算预算拓展候选；复用仍有效的基础研究，查关键变化，不每日深挖全部市场。解释经营是否仍可靠、低位原因、持续回升证据、反证、剩余上行和行业共同风险。有限覆盖不能称全市场最优。

{
  "historical_closes": {
    "600309.SH": [
      {
        "date": "2025-05-19",
        "close": "56.750",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-20",
        "close": "56.810",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-21",
        "close": "56.660",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-22",
        "close": "56.160",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-23",
        "close": "56.080",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-26",
        "close": "55.410",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-27",
        "close": "54.950",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-28",
        "close": "54.910",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-29",
        "close": "55.530",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      },
      {
        "date": "2025-05-30",
        "close": "54.140",
        "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
      }
    ]
  },
  "evidence": [],
  "candidate_research_pack": {
    "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
    "purpose": "LOW_RECOVERY",
    "cutoff_date": "2025-05-15",
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
        "symbol": "600309.SH",
        "name": "万华化学",
        "research_state": "LOW_WAITING_RECOVERY_RESEARCH",
        "attention_priority": 10,
        "attention_reasons": [
          "60/120日位置较低且5日转正，但基本面必须先确认没有实质恶化。"
        ],
        "risk_tags": [],
        "seed_snapshot": {
          "price_cny": "57.4300",
          "change_pct": null,
          "amount_cny": null,
          "source_provider": "historical daily"
        },
        "market_history": {
          "symbol": "600309.SH",
          "name": "万华化学",
          "industry": null,
          "industry_characteristics": [],
          "as_of_close": "57.4300",
          "observations": 149,
          "continuous_analysis_sessions": 149,
          "suspected_price_basis_break": null,
          "history_coverage": {
            "sessions": 149,
            "continuous_sessions": 149,
            "has_20_sessions": true,
            "has_60_sessions": true,
            "has_120_sessions": true,
            "has_250_sessions": false
          },
          "returns_pct": {
            "5_sessions": "3.5708",
            "20_sessions": "-3.3978",
            "60_sessions": "-18.4928"
          },
          "moving_average": {
            "ma5": "57.0100",
            "ma20": "55.5250",
            "ma60": "63.2637"
          },
          "range_position_0_to_1": {
            "20_sessions": "0.7957",
            "60_sessions": "0.2004",
            "120_sessions": "0.1396",
            "250_sessions": null
          },
          "annualized_volatility_pct_approx": "32.5322",
          "kline": {
            "daily_last20": [
              {
                "date": "2025-04-15",
                "open": "58.3600",
                "high": "58.3800",
                "low": "55.2200",
                "close": "56.2600",
                "volume": "669616.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-16",
                "open": "56.2700",
                "high": "56.3000",
                "low": "54.5600",
                "close": "55.3500",
                "volume": "419179.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-17",
                "open": "54.8000",
                "high": "55.2700",
                "low": "54.5800",
                "close": "54.8900",
                "volume": "344153.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-18",
                "open": "54.9100",
                "high": "55.0500",
                "low": "54.6000",
                "close": "54.9900",
                "volume": "208295.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-21",
                "open": "54.8800",
                "high": "54.8800",
                "low": "53.8900",
                "close": "54.2600",
                "volume": "340944.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-22",
                "open": "54.0000",
                "high": "54.5500",
                "low": "53.8900",
                "close": "54.0800",
                "volume": "233711.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-23",
                "open": "54.3200",
                "high": "55.6700",
                "low": "54.3200",
                "close": "55.0500",
                "volume": "396007.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-24",
                "open": "55.1700",
                "high": "55.1700",
                "low": "54.2200",
                "close": "54.4500",
                "volume": "211666.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-25",
                "open": "54.9000",
                "high": "56.9900",
                "low": "54.8900",
                "close": "56.0500",
                "volume": "486825.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-28",
                "open": "56.0500",
                "high": "56.0500",
                "low": "55.1300",
                "close": "55.1900",
                "volume": "221998.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-29",
                "open": "55.2100",
                "high": "55.2200",
                "low": "54.3400",
                "close": "54.5000",
                "volume": "217374.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-04-30",
                "open": "54.4000",
                "high": "55.1300",
                "low": "54.3000",
                "close": "54.4400",
                "volume": "167348.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-06",
                "open": "54.8800",
                "high": "55.1000",
                "low": "54.5000",
                "close": "55.0600",
                "volume": "266810.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-07",
                "open": "56.0000",
                "high": "56.1000",
                "low": "54.9700",
                "close": "55.4300",
                "volume": "266258.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-08",
                "open": "55.0200",
                "high": "55.7000",
                "low": "54.8800",
                "close": "55.4500",
                "volume": "204166.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-09",
                "open": "55.3900",
                "high": "55.3900",
                "low": "54.6800",
                "close": "54.8900",
                "volume": "178435.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-12",
                "open": "55.4900",
                "high": "57.4800",
                "low": "55.4000",
                "close": "57.4800",
                "volume": "613487.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-13",
                "open": "58.0000",
                "high": "58.1000",
                "low": "56.7800",
                "close": "56.9600",
                "volume": "338237.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-14",
                "open": "56.9500",
                "high": "58.3200",
                "low": "56.7900",
                "close": "58.2900",
                "volume": "380971.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              },
              {
                "date": "2025-05-15",
                "open": "58.0300",
                "high": "58.4200",
                "low": "57.2800",
                "close": "57.4300",
                "volume": "246833.0000",
                "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
              }
            ],
            "weekly_last12": [
              {
                "period": "2025-W09",
                "start": "2025-02-24",
                "end": "2025-02-28",
                "open": "67.8000",
                "high": "70.5900",
                "low": "66.8900",
                "close": "68.8100",
                "volume": "1096454.0000"
              },
              {
                "period": "2025-W10",
                "start": "2025-03-03",
                "end": "2025-03-07",
                "open": "68.8100",
                "high": "70.1600",
                "low": "67.8000",
                "close": "68.6200",
                "volume": "794510.0000"
              },
              {
                "period": "2025-W11",
                "start": "2025-03-10",
                "end": "2025-03-14",
                "open": "68.6200",
                "high": "70.2900",
                "low": "67.6800",
                "close": "69.8400",
                "volume": "1110416.0000"
              },
              {
                "period": "2025-W12",
                "start": "2025-03-17",
                "end": "2025-03-21",
                "open": "70.2500",
                "high": "71.7700",
                "low": "67.3600",
                "close": "67.4000",
                "volume": "1261100.0000"
              },
              {
                "period": "2025-W13",
                "start": "2025-03-24",
                "end": "2025-03-28",
                "open": "67.3600",
                "high": "69.0000",
                "low": "66.7000",
                "close": "67.7100",
                "volume": "867282.0000"
              },
              {
                "period": "2025-W14",
                "start": "2025-03-31",
                "end": "2025-04-03",
                "open": "68.0900",
                "high": "68.5500",
                "low": "65.4000",
                "close": "65.7400",
                "volume": "661792.0000"
              },
              {
                "period": "2025-W15",
                "start": "2025-04-07",
                "end": "2025-04-11",
                "open": "62.8000",
                "high": "62.8000",
                "low": "57.8800",
                "close": "60.2000",
                "volume": "1656046.0000"
              },
              {
                "period": "2025-W16",
                "start": "2025-04-14",
                "end": "2025-04-18",
                "open": "60.2400",
                "high": "60.4500",
                "low": "54.5600",
                "close": "54.9900",
                "volume": "1882275.0000"
              },
              {
                "period": "2025-W17",
                "start": "2025-04-21",
                "end": "2025-04-25",
                "open": "54.8800",
                "high": "56.9900",
                "low": "53.8900",
                "close": "56.0500",
                "volume": "1669153.0000"
              },
              {
                "period": "2025-W18",
                "start": "2025-04-28",
                "end": "2025-04-30",
                "open": "56.0500",
                "high": "56.0500",
                "low": "54.3000",
                "close": "54.4400",
                "volume": "606720.0000"
              },
              {
                "period": "2025-W19",
                "start": "2025-05-06",
                "end": "2025-05-09",
                "open": "54.8800",
                "high": "56.1000",
                "low": "54.5000",
                "close": "54.8900",
                "volume": "915669.0000"
              },
              {
                "period": "2025-W20",
                "start": "2025-05-12",
                "end": "2025-05-15",
                "open": "55.4900",
                "high": "58.4200",
                "low": "55.4000",
                "close": "57.4300",
                "volume": "1579528.0000"
              }
            ],
            "monthly_last12": [
              {
                "period": "2024-09",
                "start": "2024-09-27",
                "end": "2024-09-30",
                "open": "82.4000",
                "high": "92.9700",
                "low": "82.4000",
                "close": "91.3200",
                "volume": "686117.0000"
              },
              {
                "period": "2024-10",
                "start": "2024-10-08",
                "end": "2024-10-31",
                "open": "100.4000",
                "high": "100.4000",
                "low": "74.5600",
                "close": "75.2500",
                "volume": "5633805.0000"
              },
              {
                "period": "2024-11",
                "start": "2024-11-01",
                "end": "2024-11-29",
                "open": "75.2700",
                "high": "83.5900",
                "low": "72.3100",
                "close": "74.2900",
                "volume": "4770226.0000"
              },
              {
                "period": "2024-12",
                "start": "2024-12-02",
                "end": "2024-12-31",
                "open": "74.2000",
                "high": "76.6400",
                "low": "71.3400",
                "close": "71.3500",
                "volume": "3880761.0000"
              },
              {
                "period": "2025-01",
                "start": "2025-01-02",
                "end": "2025-01-27",
                "open": "71.3500",
                "high": "71.3500",
                "low": "65.4500",
                "close": "68.5300",
                "volume": "3235004.0000"
              },
              {
                "period": "2025-02",
                "start": "2025-02-05",
                "end": "2025-02-28",
                "open": "68.5900",
                "high": "73.9900",
                "low": "66.5000",
                "close": "68.8100",
                "volume": "4430393.0000"
              },
              {
                "period": "2025-03",
                "start": "2025-03-03",
                "end": "2025-03-31",
                "open": "68.8100",
                "high": "71.7700",
                "low": "66.7000",
                "close": "67.2100",
                "volume": "4185862.0000"
              },
              {
                "period": "2025-04",
                "start": "2025-04-01",
                "end": "2025-04-30",
                "open": "67.2200",
                "high": "67.6400",
                "low": "53.8900",
                "close": "54.4400",
                "volume": "6323432.0000"
              },
              {
                "period": "2025-05",
                "start": "2025-05-06",
                "end": "2025-05-15",
                "open": "54.8800",
                "high": "58.4200",
                "low": "54.5000",
                "close": "57.4300",
                "volume": "2495197.0000"
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
    "date": "2025-05-30",
    "revision": 1,
    "candidate_watchlist": [],
    "last_candidate_pack": {
      "path": "research/2025-05-30/candidate_pack.json",
      "sha256": "5690fc66c026024eb5f3bc135d6313f2391b72654d331eaaf1b09342e027b388",
      "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
      "purpose": "LOW_RECOVERY",
      "candidate_count": 1,
      "not_a_recommendation": true
    },
    "last_broad_universe_source": null,
    "formal_research_enabled": null,
    "last_decision_summary": null,
    "note": "AI_SELECT research state only; never an order, holding or recommendation. Simulation state is isolated from FORMAL.",
    "last_research_payload_sha256": "ed3772ee73b22cfa878402de83a4da0c5c923dc36bc8a36b14c229c3bddcd9a5",
    "universe_scope": {
      "authorized_symbols": [
        "600309.SH"
      ],
      "coverage": "FIXED_HISTORICAL_PILOT_UNIVERSE_CANDIDATE",
      "not_full_a_share_claim": true
    }
  },
  "universe_scope": {
    "authorized_symbols": [
      "600309.SH"
    ],
    "coverage": "FIXED_HISTORICAL_PILOT_UNIVERSE_CANDIDATE",
    "not_full_a_share_claim": true
  },
  "official_disclosure_pack": {
    "kind": "OFFICIAL_DISCLOSURE_PACK",
    "symbols_requested": [
      "600309.SH"
    ],
    "results": [
      {
        "symbol": "600309.SH",
        "provider_status": "OK",
        "items": [
          {
            "symbol": "600309.SH",
            "title": "万华化学2025年第一季度报告",
            "published_at": "2025-04-15T00:00:00+08:00",
            "source_official": true,
            "source_provider": "CNINFO",
            "document_url": "https://static.cninfo.com.cn/finalpage/2025-04-15/1223097314.PDF",
            "is_periodic_report_body": true,
            "category": "PERIODIC_REPORT"
          }
        ]
      }
    ],
    "latest_periodic_report_refs": [
      {
        "symbol": "600309.SH",
        "title": "万华化学2025年第一季度报告",
        "published_at": "2025-04-15T00:00:00+08:00",
        "source_official": true,
        "source_provider": "CNINFO",
        "document_url": "https://static.cninfo.com.cn/finalpage/2025-04-15/1223097314.PDF",
        "is_periodic_report_body": true,
        "category": "PERIODIC_REPORT"
      }
    ],
    "important_recent_refs": []
  },
  "financial_reviews": {
    "600309.SH": {
      "status": "REVIEWED",
      "symbol": "600309.SH",
      "as_of": "2025-05-15T14:40:00+08:00",
      "source_report": "https://static.cninfo.com.cn/finalpage/2025-04-15/1223097314.PDF",
      "source_official": true,
      "period": "2025Q1",
      "facts": [
        {
          "name": "营业收入",
          "value": "43,067,850,762.48 CNY，同比 -6.70%",
          "source": "万华化学2025年第一季度报告"
        },
        {
          "name": "归母净利润",
          "value": "3,082,066,208.03 CNY，同比 -25.87%",
          "source": "万华化学2025年第一季度报告"
        },
        {
          "name": "扣非归母净利润",
          "value": "3,040,424,946.53 CNY，同比 -26.33%",
          "source": "万华化学2025年第一季度报告"
        },
        {
          "name": "经营活动现金流量净额",
          "value": "581,158,509.58 CNY，同比 -81.15%",
          "source": "万华化学2025年第一季度报告"
        }
      ],
      "summary": "股价处相对低位并出现短期企稳，但2025Q1收入、利润和经营现金流均明显下滑，不能仅凭低位/反弹认定基本面未受损。D02应降低买入意愿，等待经营数据改善。",
      "data_gaps": [
        "未纳入完整产品价差与行业库存日频数据。"
      ]
    }
  },
  "news_research": {
    "status": "NO_RELEVANT_RECENT_NEWS",
    "searched_at": "2025-05-15T14:50:00+08:00",
    "items": [],
    "data_gaps": [
      "Historical news coverage is intentionally limited; absence of a captured item does not prove no news existed."
    ]
  },
  "decision_research_bundle": {
    "kind": "DECISION_RESEARCH_BUNDLE",
    "as_of": "2025-05-30T15:00:00+08:00",
    "symbols": [
      "600309.SH"
    ],
    "candidate_research_pack": {
      "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
      "purpose": "LOW_RECOVERY",
      "cutoff_date": "2025-05-15",
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
          "symbol": "600309.SH",
          "name": "万华化学",
          "research_state": "LOW_WAITING_RECOVERY_RESEARCH",
          "attention_priority": 10,
          "attention_reasons": [
            "60/120日位置较低且5日转正，但基本面必须先确认没有实质恶化。"
          ],
          "risk_tags": [],
          "seed_snapshot": {
            "price_cny": "57.4300",
            "change_pct": null,
            "amount_cny": null,
            "source_provider": "historical daily"
          },
          "market_history": {
            "symbol": "600309.SH",
            "name": "万华化学",
            "industry": null,
            "industry_characteristics": [],
            "as_of_close": "57.4300",
            "observations": 149,
            "continuous_analysis_sessions": 149,
            "suspected_price_basis_break": null,
            "history_coverage": {
              "sessions": 149,
              "continuous_sessions": 149,
              "has_20_sessions": true,
              "has_60_sessions": true,
              "has_120_sessions": true,
              "has_250_sessions": false
            },
            "returns_pct": {
              "5_sessions": "3.5708",
              "20_sessions": "-3.3978",
              "60_sessions": "-18.4928"
            },
            "moving_average": {
              "ma5": "57.0100",
              "ma20": "55.5250",
              "ma60": "63.2637"
            },
            "range_position_0_to_1": {
              "20_sessions": "0.7957",
              "60_sessions": "0.2004",
              "120_sessions": "0.1396",
              "250_sessions": null
            },
            "annualized_volatility_pct_approx": "32.5322",
            "kline": {
              "daily_last20": [
                {
                  "date": "2025-04-15",
                  "open": "58.3600",
                  "high": "58.3800",
                  "low": "55.2200",
                  "close": "56.2600",
                  "volume": "669616.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-16",
                  "open": "56.2700",
                  "high": "56.3000",
                  "low": "54.5600",
                  "close": "55.3500",
                  "volume": "419179.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-17",
                  "open": "54.8000",
                  "high": "55.2700",
                  "low": "54.5800",
                  "close": "54.8900",
                  "volume": "344153.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-18",
                  "open": "54.9100",
                  "high": "55.0500",
                  "low": "54.6000",
                  "close": "54.9900",
                  "volume": "208295.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-21",
                  "open": "54.8800",
                  "high": "54.8800",
                  "low": "53.8900",
                  "close": "54.2600",
                  "volume": "340944.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-22",
                  "open": "54.0000",
                  "high": "54.5500",
                  "low": "53.8900",
                  "close": "54.0800",
                  "volume": "233711.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-23",
                  "open": "54.3200",
                  "high": "55.6700",
                  "low": "54.3200",
                  "close": "55.0500",
                  "volume": "396007.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-24",
                  "open": "55.1700",
                  "high": "55.1700",
                  "low": "54.2200",
                  "close": "54.4500",
                  "volume": "211666.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-25",
                  "open": "54.9000",
                  "high": "56.9900",
                  "low": "54.8900",
                  "close": "56.0500",
                  "volume": "486825.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-28",
                  "open": "56.0500",
                  "high": "56.0500",
                  "low": "55.1300",
                  "close": "55.1900",
                  "volume": "221998.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-29",
                  "open": "55.2100",
                  "high": "55.2200",
                  "low": "54.3400",
                  "close": "54.5000",
                  "volume": "217374.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-04-30",
                  "open": "54.4000",
                  "high": "55.1300",
                  "low": "54.3000",
                  "close": "54.4400",
                  "volume": "167348.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-06",
                  "open": "54.8800",
                  "high": "55.1000",
                  "low": "54.5000",
                  "close": "55.0600",
                  "volume": "266810.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-07",
                  "open": "56.0000",
                  "high": "56.1000",
                  "low": "54.9700",
                  "close": "55.4300",
                  "volume": "266258.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-08",
                  "open": "55.0200",
                  "high": "55.7000",
                  "low": "54.8800",
                  "close": "55.4500",
                  "volume": "204166.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-09",
                  "open": "55.3900",
                  "high": "55.3900",
                  "low": "54.6800",
                  "close": "54.8900",
                  "volume": "178435.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-12",
                  "open": "55.4900",
                  "high": "57.4800",
                  "low": "55.4000",
                  "close": "57.4800",
                  "volume": "613487.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-13",
                  "open": "58.0000",
                  "high": "58.1000",
                  "low": "56.7800",
                  "close": "56.9600",
                  "volume": "338237.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-14",
                  "open": "56.9500",
                  "high": "58.3200",
                  "low": "56.7900",
                  "close": "58.2900",
                  "volume": "380971.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                },
                {
                  "date": "2025-05-15",
                  "open": "58.0300",
                  "high": "58.4200",
                  "low": "57.2800",
                  "close": "57.4300",
                  "volume": "246833.0000",
                  "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-09-27%2C2025-10-31%2C320%2C"
                }
              ],
              "weekly_last12": [
                {
                  "period": "2025-W09",
                  "start": "2025-02-24",
                  "end": "2025-02-28",
                  "open": "67.8000",
                  "high": "70.5900",
                  "low": "66.8900",
                  "close": "68.8100",
                  "volume": "1096454.0000"
                },
                {
                  "period": "2025-W10",
                  "start": "2025-03-03",
                  "end": "2025-03-07",
                  "open": "68.8100",
                  "high": "70.1600",
                  "low": "67.8000",
                  "close": "68.6200",
                  "volume": "794510.0000"
                },
                {
                  "period": "2025-W11",
                  "start": "2025-03-10",
                  "end": "2025-03-14",
                  "open": "68.6200",
                  "high": "70.2900",
                  "low": "67.6800",
                  "close": "69.8400",
                  "volume": "1110416.0000"
                },
                {
                  "period": "2025-W12",
                  "start": "2025-03-17",
                  "end": "2025-03-21",
                  "open": "70.2500",
                  "high": "71.7700",
                  "low": "67.3600",
                  "close": "67.4000",
                  "volume": "1261100.0000"
                },
                {
                  "period": "2025-W13",
                  "start": "2025-03-24",
                  "end": "2025-03-28",
                  "open": "67.3600",
                  "high": "69.0000",
                  "low": "66.7000",
                  "close": "67.7100",
                  "volume": "867282.0000"
                },
                {
                  "period": "2025-W14",
                  "start": "2025-03-31",
                  "end": "2025-04-03",
                  "open": "68.0900",
                  "high": "68.5500",
                  "low": "65.4000",
                  "close": "65.7400",
                  "volume": "661792.0000"
                },
                {
                  "period": "2025-W15",
                  "start": "2025-04-07",
                  "end": "2025-04-11",
                  "open": "62.8000",
                  "high": "62.8000",
                  "low": "57.8800",
                  "close": "60.2000",
                  "volume": "1656046.0000"
                },
                {
                  "period": "2025-W16",
                  "start": "2025-04-14",
                  "end": "2025-04-18",
                  "open": "60.2400",
                  "high": "60.4500",
                  "low": "54.5600",
                  "close": "54.9900",
                  "volume": "1882275.0000"
                },
                {
                  "period": "2025-W17",
                  "start": "2025-04-21",
                  "end": "2025-04-25",
                  "open": "54.8800",
                  "high": "56.9900",
                  "low": "53.8900",
                  "close": "56.0500",
                  "volume": "1669153.0000"
                },
                {
                  "period": "2025-W18",
                  "start": "2025-04-28",
                  "end": "2025-04-30",
                  "open": "56.0500",
                  "high": "56.0500",
                  "low": "54.3000",
                  "close": "54.4400",
                  "volume": "606720.0000"
                },
                {
                  "period": "2025-W19",
                  "start": "2025-05-06",
                  "end": "2025-05-09",
                  "open": "54.8800",
                  "high": "56.1000",
                  "low": "54.5000",
                  "close": "54.8900",
                  "volume": "915669.0000"
                },
                {
                  "period": "2025-W20",
                  "start": "2025-05-12",
                  "end": "2025-05-15",
                  "open": "55.4900",
                  "high": "58.4200",
                  "low": "55.4000",
                  "close": "57.4300",
                  "volume": "1579528.0000"
                }
              ],
              "monthly_last12": [
                {
                  "period": "2024-09",
                  "start": "2024-09-27",
                  "end": "2024-09-30",
                  "open": "82.4000",
                  "high": "92.9700",
                  "low": "82.4000",
                  "close": "91.3200",
                  "volume": "686117.0000"
                },
                {
                  "period": "2024-10",
                  "start": "2024-10-08",
                  "end": "2024-10-31",
                  "open": "100.4000",
                  "high": "100.4000",
                  "low": "74.5600",
                  "close": "75.2500",
                  "volume": "5633805.0000"
                },
                {
                  "period": "2024-11",
                  "start": "2024-11-01",
                  "end": "2024-11-29",
                  "open": "75.2700",
                  "high": "83.5900",
                  "low": "72.3100",
                  "close": "74.2900",
                  "volume": "4770226.0000"
                },
                {
                  "period": "2024-12",
                  "start": "2024-12-02",
                  "end": "2024-12-31",
                  "open": "74.2000",
                  "high": "76.6400",
                  "low": "71.3400",
                  "close": "71.3500",
                  "volume": "3880761.0000"
                },
                {
                  "period": "2025-01",
                  "start": "2025-01-02",
                  "end": "2025-01-27",
                  "open": "71.3500",
                  "high": "71.3500",
                  "low": "65.4500",
                  "close": "68.5300",
                  "volume": "3235004.0000"
                },
                {
                  "period": "2025-02",
                  "start": "2025-02-05",
                  "end": "2025-02-28",
                  "open": "68.5900",
                  "high": "73.9900",
                  "low": "66.5000",
                  "close": "68.8100",
                  "volume": "4430393.0000"
                },
                {
                  "period": "2025-03",
                  "start": "2025-03-03",
                  "end": "2025-03-31",
                  "open": "68.8100",
                  "high": "71.7700",
                  "low": "66.7000",
                  "close": "67.2100",
                  "volume": "4185862.0000"
                },
                {
                  "period": "2025-04",
                  "start": "2025-04-01",
                  "end": "2025-04-30",
                  "open": "67.2200",
                  "high": "67.6400",
                  "low": "53.8900",
                  "close": "54.4400",
                  "volume": "6323432.0000"
                },
                {
                  "period": "2025-05",
                  "start": "2025-05-06",
                  "end": "2025-05-15",
                  "open": "54.8800",
                  "high": "58.4200",
                  "low": "54.5000",
                  "close": "57.4300",
                  "volume": "2495197.0000"
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
      "date": "2025-05-30",
      "revision": 1,
      "candidate_watchlist": [],
      "last_candidate_pack": {
        "path": "research/2025-05-30/candidate_pack.json",
        "sha256": "5690fc66c026024eb5f3bc135d6313f2391b72654d331eaaf1b09342e027b388",
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": "LOW_RECOVERY",
        "candidate_count": 1,
        "not_a_recommendation": true
      },
      "last_broad_universe_source": null,
      "formal_research_enabled": null,
      "last_decision_summary": null,
      "note": "AI_SELECT research state only; never an order, holding or recommendation. Simulation state is isolated from FORMAL.",
      "last_research_payload_sha256": "ed3772ee73b22cfa878402de83a4da0c5c923dc36bc8a36b14c229c3bddcd9a5",
      "universe_scope": {
        "authorized_symbols": [
          "600309.SH"
        ],
        "coverage": "FIXED_HISTORICAL_PILOT_UNIVERSE_CANDIDATE",
        "not_full_a_share_claim": true
      }
    },
    "market_context": {
      "mode": "SIMULATION",
      "visible_symbols": [
        "600309.SH"
      ],
      "fidelity": "BOUNDED_CANDIDATE_REAL_DAILY"
    },
    "per_symbol": [
      {
        "symbol": "600309.SH",
        "official_disclosure_status": "OK",
        "latest_periodic_report_ref": {
          "symbol": "600309.SH",
          "title": "万华化学2025年第一季度报告",
          "published_at": "2025-04-15T00:00:00+08:00",
          "source_official": true,
          "source_provider": "CNINFO",
          "document_url": "https://static.cninfo.com.cn/finalpage/2025-04-15/1223097314.PDF",
          "is_periodic_report_body": true,
          "category": "PERIODIC_REPORT"
        },
        "important_official_disclosures": [],
        "financial_review": {
          "status": "REVIEWED",
          "symbol": "600309.SH",
          "as_of": "2025-05-15T14:40:00+08:00",
          "source_report": "https://static.cninfo.com.cn/finalpage/2025-04-15/1223097314.PDF",
          "source_official": true,
          "period": "2025Q1",
          "facts": [
            {
              "name": "营业收入",
              "value": "43,067,850,762.48 CNY，同比 -6.70%",
              "source": "万华化学2025年第一季度报告"
            },
            {
              "name": "归母净利润",
              "value": "3,082,066,208.03 CNY，同比 -25.87%",
              "source": "万华化学2025年第一季度报告"
            },
            {
              "name": "扣非归母净利润",
              "value": "3,040,424,946.53 CNY，同比 -26.33%",
              "source": "万华化学2025年第一季度报告"
            },
            {
              "name": "经营活动现金流量净额",
              "value": "581,158,509.58 CNY，同比 -81.15%",
              "source": "万华化学2025年第一季度报告"
            }
          ],
          "summary": "股价处相对低位并出现短期企稳，但2025Q1收入、利润和经营现金流均明显下滑，不能仅凭低位/反弹认定基本面未受损。D02应降低买入意愿，等待经营数据改善。",
          "data_gaps": [
            "未纳入完整产品价差与行业库存日频数据。"
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
    "path": "research-inputs\\D02\\2025-05-30",
    "information_cutoff": "2025-05-15T15:00:00+08:00",
    "file_sha256": {
      "manifest.json": "6e53e0ca8e99a85b59778c4ff15ca7faad600bbe8683472dedd73f664e69454f",
      "official-disclosure-pack.json": "3f3efa28febf53981649a9498efea3c16b3200be4465c4b6ed95b412a3670c91",
      "financial-reviews.json": "2aa2f64e3f8a855b048ef0fe0deb722aa5a45aa96b6a9ffc20da36c2929afb0f",
      "news-research.json": "d4a67899157322d422155dfa6f941f7ca7f6f2c06e17775841f29ba297b824f2",
      "candidate-research-pack.json": "5690fc66c026024eb5f3bc135d6313f2391b72654d331eaaf1b09342e027b388",
      "universe-scope.json": "34993366849809d17bdebff1aff30855ce44c8ece83592d7330aa1c43946b6e8"
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
你现在回到2025-05-30收盘时。请把自己视为当时的投资研究者。你只能使用2025-05-30收盘及以前已经可见的市场资料，不知道之后任何价格、涨跌、财报结果或事件。不要用后验结果修正当时判断。 本日线近似将在下一交易日2025-06-03开盘模拟执行。

下面数据均按knowledge_cutoff裁剪。把它们当作你在那个时点能看到的大致市场环境；新闻缺失可忽略，不允许根据后来的结果补全。

{
  "mode": "TIME_TRAVEL",
  "target_date": "2025-05-30",
  "knowledge_cutoff": "2025-05-30T15:00:00+08:00",
  "planned_execution_date": "2025-06-03",
  "instruction": "你现在回到2025-05-30收盘时。请把自己视为当时的投资研究者。你只能使用2025-05-30收盘及以前已经可见的市场资料，不知道之后任何价格、涨跌、财报结果或事件。不要用后验结果修正当时判断。 本日线近似将在下一交易日2025-06-03开盘模拟执行。",
  "news_policy": "IGNORE_ARCHIVED_NEWS_BY_DEFAULT",
  "market_proxy": {
    "kind": "CONFIGURED_UNIVERSE_EQUAL_WEIGHT_PROXY_NOT_BROAD_MARKET_INDEX",
    "returns_pct": {
      "5_sessions": "-3.4593",
      "20_sessions": "-0.6606",
      "60_sessions": "-21.5021"
    }
  },
  "symbols": [
    {
      "symbol": "600309.SH",
      "name": "万华化学",
      "industry": null,
      "industry_characteristics": [],
      "as_of_close": "54.1400",
      "observations": 203,
      "continuous_analysis_sessions": 203,
      "suspected_price_basis_break": null,
      "history_coverage": {
        "sessions": 203,
        "continuous_sessions": 203,
        "has_20_sessions": true,
        "has_60_sessions": true,
        "has_120_sessions": true,
        "has_250_sessions": false
      },
      "returns_pct": {
        "5_sessions": "-3.4593",
        "20_sessions": "-0.6606",
        "60_sessions": "-21.5021"
      },
      "moving_average": {
        "ma5": "54.9880",
        "ma20": "55.9830",
        "ma60": "60.8863"
      },
      "range_position_0_to_1": {
        "20_sessions": "0.0000",
        "60_sessions": "0.0036",
        "120_sessions": "0.0027",
        "250_sessions": null
      },
      "annualized_volatility_pct_approx": "23.8482",
      "kline": {
        "daily_last20": [
          {
            "date": "2025-04-30",
            "open": "54.4000",
            "high": "55.1300",
            "low": "54.3000",
            "close": "54.4400",
            "volume": "167348.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-06",
            "open": "54.8800",
            "high": "55.1000",
            "low": "54.5000",
            "close": "55.0600",
            "volume": "266810.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-07",
            "open": "56.0000",
            "high": "56.1000",
            "low": "54.9700",
            "close": "55.4300",
            "volume": "266258.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-08",
            "open": "55.0200",
            "high": "55.7000",
            "low": "54.8800",
            "close": "55.4500",
            "volume": "204166.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-09",
            "open": "55.3900",
            "high": "55.3900",
            "low": "54.6800",
            "close": "54.8900",
            "volume": "178435.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-12",
            "open": "55.4900",
            "high": "57.4800",
            "low": "55.4000",
            "close": "57.4800",
            "volume": "613487.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-13",
            "open": "58.0000",
            "high": "58.1000",
            "low": "56.7800",
            "close": "56.9600",
            "volume": "338237.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-14",
            "open": "56.9500",
            "high": "58.3200",
            "low": "56.7900",
            "close": "58.2900",
            "volume": "380971.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-15",
            "open": "58.0300",
            "high": "58.4200",
            "low": "57.2800",
            "close": "57.4300",
            "volume": "246833.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-16",
            "open": "57.1500",
            "high": "57.1900",
            "low": "56.6200",
            "close": "56.8300",
            "volume": "186263.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-19",
            "open": "56.8300",
            "high": "56.9400",
            "low": "56.1500",
            "close": "56.7500",
            "volume": "143920.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-20",
            "open": "56.6600",
            "high": "57.0900",
            "low": "56.3100",
            "close": "56.8100",
            "volume": "142921.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-21",
            "open": "56.5400",
            "high": "57.0600",
            "low": "56.5100",
            "close": "56.6600",
            "volume": "128649.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-22",
            "open": "56.6000",
            "high": "56.6000",
            "low": "56.0400",
            "close": "56.1600",
            "volume": "130734.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-23",
            "open": "56.2200",
            "high": "57.0500",
            "low": "56.0600",
            "close": "56.0800",
            "volume": "215234.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-26",
            "open": "56.0900",
            "high": "56.1900",
            "low": "55.3300",
            "close": "55.4100",
            "volume": "185026.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-27",
            "open": "55.4300",
            "high": "55.5300",
            "low": "54.9000",
            "close": "54.9500",
            "volume": "142351.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-28",
            "open": "55.1100",
            "high": "55.1400",
            "low": "54.8800",
            "close": "54.9100",
            "volume": "96507.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-29",
            "open": "54.9800",
            "high": "55.5300",
            "low": "54.6500",
            "close": "55.5300",
            "volume": "143998.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          },
          {
            "date": "2025-05-30",
            "open": "54.8800",
            "high": "54.8800",
            "low": "53.9200",
            "close": "54.1400",
            "volume": "150576.0000",
            "source": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600309%2Cday%2C2024-07-26%2C2025-08-29%2C320%2C"
          }
        ],
        "weekly_last12": [
          {
            "period": "2025-W11",
            "start": "2025-03-10",
            "end": "2025-03-14",
            "open": "68.6200",
            "high": "70.2900",
            "low": "67.6800",
            "close": "69.8400",
            "volume": "1110416.0000"
          },
          {
            "period": "2025-W12",
            "start": "2025-03-17",
            "end": "2025-03-21",
            "open": "70.2500",
            "high": "71.7700",
            "low": "67.3600",
            "close": "67.4000",
            "volume": "1261100.0000"
          },
          {
            "period": "2025-W13",
            "start": "2025-03-24",
            "end": "2025-03-28",
            "open": "67.3600",
            "high": "69.0000",
            "low": "66.7000",
            "close": "67.7100",
            "volume": "867282.0000"
          },
          {
            "period": "2025-W14",
            "start": "2025-03-31",
            "end": "2025-04-03",
            "open": "68.0900",
            "high": "68.5500",
            "low": "65.4000",
            "close": "65.7400",
            "volume": "661792.0000"
          },
          {
            "period": "2025-W15",
            "start": "2025-04-07",
            "end": "2025-04-11",
            "open": "62.8000",
            "high": "62.8000",
            "low": "57.8800",
            "close": "60.2000",
            "volume": "1656046.0000"
          },
          {
            "period": "2025-W16",
            "start": "2025-04-14",
            "end": "2025-04-18",
            "open": "60.2400",
            "high": "60.4500",
            "low": "54.5600",
            "close": "54.9900",
            "volume": "1882275.0000"
          },
          {
            "period": "2025-W17",
            "start": "2025-04-21",
            "end": "2025-04-25",
            "open": "54.8800",
            "high": "56.9900",
            "low": "53.8900",
            "close": "56.0500",
            "volume": "1669153.0000"
          },
          {
            "period": "2025-W18",
            "start": "2025-04-28",
            "end": "2025-04-30",
            "open": "56.0500",
            "high": "56.0500",
            "low": "54.3000",
            "close": "54.4400",
            "volume": "606720.0000"
          },
          {
            "period": "2025-W19",
            "start": "2025-05-06",
            "end": "2025-05-09",
            "open": "54.8800",
            "high": "56.1000",
            "low": "54.5000",
            "close": "54.8900",
            "volume": "915669.0000"
          },
          {
            "period": "2025-W20",
            "start": "2025-05-12",
            "end": "2025-05-16",
            "open": "55.4900",
            "high": "58.4200",
            "low": "55.4000",
            "close": "56.8300",
            "volume": "1765791.0000"
          },
          {
            "period": "2025-W21",
            "start": "2025-05-19",
            "end": "2025-05-23",
            "open": "56.8300",
            "high": "57.0900",
            "low": "56.0400",
            "close": "56.0800",
            "volume": "761458.0000"
          },
          {
            "period": "2025-W22",
            "start": "2025-05-26",
            "end": "2025-05-30",
            "open": "56.0900",
            "high": "56.1900",
            "low": "53.9200",
            "close": "54.1400",
            "volume": "718458.0000"
          }
        ],
        "monthly_last12": [
          {
            "period": "2024-07",
            "start": "2024-07-26",
            "end": "2024-07-31",
            "open": "78.9000",
            "high": "80.3000",
            "low": "74.3800",
            "close": "77.6000",
            "volume": "466737.0000"
          },
          {
            "period": "2024-08",
            "start": "2024-08-01",
            "end": "2024-08-30",
            "open": "77.5000",
            "high": "77.6200",
            "low": "69.1700",
            "close": "73.0000",
            "volume": "2944233.0000"
          },
          {
            "period": "2024-09",
            "start": "2024-09-02",
            "end": "2024-09-30",
            "open": "72.8000",
            "high": "92.9700",
            "low": "68.9000",
            "close": "91.3200",
            "volume": "2882558.0000"
          },
          {
            "period": "2024-10",
            "start": "2024-10-08",
            "end": "2024-10-31",
            "open": "100.4000",
            "high": "100.4000",
            "low": "74.5600",
            "close": "75.2500",
            "volume": "5633805.0000"
          },
          {
            "period": "2024-11",
            "start": "2024-11-01",
            "end": "2024-11-29",
            "open": "75.2700",
            "high": "83.5900",
            "low": "72.3100",
            "close": "74.2900",
            "volume": "4770226.0000"
          },
          {
            "period": "2024-12",
            "start": "2024-12-02",
            "end": "2024-12-31",
            "open": "74.2000",
            "high": "76.6400",
            "low": "71.3400",
            "close": "71.3500",
            "volume": "3880761.0000"
          },
          {
            "period": "2025-01",
            "start": "2025-01-02",
            "end": "2025-01-27",
            "open": "71.3500",
            "high": "71.3500",
            "low": "65.4500",
            "close": "68.5300",
            "volume": "3235004.0000"
          },
          {
            "period": "2025-02",
            "start": "2025-02-05",
            "end": "2025-02-28",
            "open": "68.5900",
            "high": "73.9900",
            "low": "66.5000",
            "close": "68.8100",
            "volume": "4430393.0000"
          },
          {
            "period": "2025-03",
            "start": "2025-03-03",
            "end": "2025-03-31",
            "open": "68.8100",
            "high": "71.7700",
            "low": "66.7000",
            "close": "67.2100",
            "volume": "4185862.0000"
          },
          {
            "period": "2025-04",
            "start": "2025-04-01",
            "end": "2025-04-30",
            "open": "67.2200",
            "high": "67.6400",
            "low": "53.8900",
            "close": "54.4400",
            "volume": "6323432.0000"
          },
          {
            "period": "2025-05",
            "start": "2025-05-06",
            "end": "2025-05-30",
            "open": "54.8800",
            "high": "58.4200",
            "low": "53.9200",
            "close": "54.1400",
            "volume": "4161376.0000"
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
