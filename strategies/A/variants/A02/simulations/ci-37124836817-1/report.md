# 模拟验证报告（不是投资成绩）

```json
{
  "variant": "A02",
  "test_id": "ci-37124836817-1",
  "data_kind": "TEST_ONLY",
  "fidelity": "ENGINEERING_ONLY",
  "completed_days": 5,
  "requested_days": 5,
  "complete": true,
  "initial_equity_cny": "200000.00",
  "final_equity_cny": "202895.80",
  "net_pnl_cny": "2895.80",
  "return_pct": "1.447900",
  "max_daily_drawdown_pct": "0",
  "fees_cny": "24.20",
  "fills": 4,
  "limitations": [
    "Synthetic prices and scripted decisions; not an AI investment test."
  ],
  "not_investment_validation": true,
  "start_date": "2025-08-01",
  "end_date": "2025-08-08",
  "annualized_return_pct": 106.37177370332572,
  "annualization": {
    "formula": "(1 + return)^(252/sessions) - 1",
    "interpretation": "数学换算，不是未来一年收益预测",
    "sessions_per_year": 252,
    "sessions": 5
  },
  "benchmark": "OPENING_PORTFOLIO_HOLD_OR_CASH",
  "benchmark_return_pct": "1.4500",
  "excess_return_percentage_points": "-0.002100",
  "win_rate_pct": null,
  "win_rate_basis": "FIFO_REALIZED_SELL_ORDERS_OF_IN_TEST_BUYS_AFTER_FEES",
  "future_data_check": "PASS_PRICE_EVIDENCE_BOUNDARY",
  "future_data_check_scope": "Persisted request price dates and evidence publication timestamps; model prior knowledge is not audited",
  "winning_sell_orders": 0,
  "eligible_sell_orders": 0,
  "excluded_opening_position_sell_orders": 2
}
```
