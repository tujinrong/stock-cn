"""Outcome-only metrics; never import these into decision rendering."""
import math
from decimal import Decimal


ANNUALIZATION = {
    "formula": "(1 + return)^(252/sessions) - 1",
    "interpretation": "数学换算，不是未来一年收益预测",
    "sessions_per_year": 252,
}


def annualized_pct(return_pct, sessions):
    if return_pct is None or sessions <= 0:
        return None
    gross = 1 + float(return_pct) / 100
    if gross < 0:
        return None
    try:
        value = (math.pow(gross, 252 / sessions) - 1) * 100
    except OverflowError:
        return None
    return value if math.isfinite(value) else None


def max_drawdown_pct(values):
    peak = values[0]
    drawdown = 0
    for value in values:
        peak = max(peak, value)
        drawdown = max(drawdown, 1 - value / peak)
    return float(drawdown * 100)


def realized_sell_win_rate(events):
    """FIFO sales of shares acquired in this run, including both sides' fees.

    Opening holdings have no verifiable historical acquisition costs. A sale
    containing any opening shares is excluded rather than assigned a fake win.
    Partial sells are measured as completed sell orders, not full round trips.
    """
    lots = {}
    for p in events[0]['after']['positions']:
        lots[p['symbol']] = [[p['quantity'], Decimal(0), False]]
    wins = counted = excluded = 0
    for e in events[1:]:
        execution = e.get('details', {}).get('execution', {})
        if execution.get('status') != 'FILLED':
            continue
        f = execution['fill']
        qty = f['quantity']
        price = Decimal(str(f['price_cny']))
        fee = Decimal(str(f['fee_cny']))
        queue = lots.setdefault(f['symbol'], [])
        if f['side'] == 'BUY':
            queue.append([qty, price + fee / qty, True])
            continue
        remaining, cost, known = qty, Decimal(0), True
        while remaining and queue:
            lot = queue[0]
            take = min(remaining, lot[0])
            cost += take * lot[1]
            known = known and lot[2]
            lot[0] -= take
            remaining -= take
            if not lot[0]:
                queue.pop(0)
        if not known or remaining:
            excluded += 1
        else:
            counted += 1
            wins += price * qty - fee > cost
    return {'win_rate_pct': 100 * wins / counted if counted else None,
            'win_rate_basis': 'FIFO_REALIZED_SELL_ORDERS_OF_IN_TEST_BUYS_AFTER_FEES',
            'winning_sell_orders': wins, 'eligible_sell_orders': counted,
            'excluded_opening_position_sell_orders': excluded}


def comparison_markdown(rows):
    lines = ["|策略/变体|测试区间|评分状态|总收益|年化收益|最大回撤|胜率|交易次数|HOLD基准收益|超额收益（百分点）|未来数据检查|",
             "|---|---|---|---:|---:|---:|---|---:|---:|---:|---|"]
    def pct(value):
        return "—" if value is None else f"{float(value):+.4f}%"
    for r in rows:
        completed = r.get('completed_days')
        days = '—' if completed is None else str(completed)
        lines.append(f"|{r['variant'][0]}/{r['variant']}|{r.get('start_date', '—')} → {r.get('end_date', '—')} ({days}交易日)|"
                     f"{r.get('score_status', 'COMPLETED')}|{pct(r.get('return_pct'))}|{pct(r.get('annualized_return_pct'))}|{pct(r.get('max_daily_drawdown_pct'))}|"
                     f"{pct(r.get('win_rate_pct'))}|{r.get('fills', '—')}|{pct(r.get('benchmark_return_pct'))}|"
                     f"{pct(r.get('excess_return_percentage_points'))}|{r.get('future_data_check', 'NOT_CHECKED')}|")
    return "\n".join(lines) + "\n\n年化按实际完成交易日复合换算，仅为数学换算，不是未来一年收益预测。连续模拟胜率按FIFO配对、扣买卖费用后的已实现卖单计算；涉及假定期初持股的卖单排除。无合格卖单或旧记录缺配对资料时为空，不能用上涨天数冒充胜率。\n"
