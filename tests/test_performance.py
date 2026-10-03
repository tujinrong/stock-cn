from decimal import Decimal

import pytest
from test_simulation import repo
from stock_cn.performance import annualized_pct
from stock_cn.performance import realized_sell_win_rate
from stock_cn.sim_data import fixture
from stock_cn.sim_agents import ScriptedSmokeAgent
from stock_cn.simulation import Simulation


def test_annualization_uses_actual_sessions_and_handles_loss():
    assert annualized_pct(10, 252) == pytest.approx(10)
    assert annualized_pct(10, 40) == pytest.approx((1.1 ** (252 / 40) - 1) * 100)
    assert annualized_pct(-100, 40) == -100
    assert annualized_pct(-101, 40) is None
    assert annualized_pct(1, 0) is None
    assert annualized_pct(1e308, 1) is None


def test_report_partial_window_hold_benchmark_and_request_boundary(repo):
    sim = Simulation(repo, 'A', 'A02', 'metrics', fixture())
    sim.run_day('2025-08-04', ScriptedSmokeAgent())
    r = sim.report()
    assert r['completed_days'] == 1 and not r['complete']
    assert r['annualized_return_pct'] == pytest.approx(annualized_pct(r['return_pct'], 1))
    assert r['start_date'] == '2025-08-01' and r['end_date'] == '2025-08-04'
    opening = sim.store.events()[0]['after']
    hold = Decimal(opening['cash_cny']) + sum(
        p['quantity'] * Decimal(sim.bar(r['end_date'], p['symbol'])['close'])
        for p in opening['positions'])
    assert Decimal(r['benchmark_return_pct']) == (hold / Decimal('200000') - 1) * 100
    assert r['future_data_check'] == 'PASS_PRICE_EVIDENCE_BOUNDARY'
    assert r['win_rate_pct'] is None
    from stock_cn.simulation import read_json
    request = read_json(sim.store.path('requests/2025-08-04/request.json'))
    next(iter(request['market'].values()))[0]['date'] = '2099-01-01'
    sim.store.write('requests/2025-08-04/request.json', request)
    assert sim.report()['future_data_check'] == 'FAIL'


def test_realized_win_rate_includes_fees_and_excludes_opening_costs():
    def event(side, quantity, price, fee):
        return {'details': {'execution': {'status': 'FILLED', 'fill': {
            'symbol': 'X', 'side': side, 'quantity': quantity,
            'price_cny': price, 'fee_cny': fee}}}}
    opening = {'after': {'positions': [{'symbol':'X', 'quantity':100}]}}
    events = [opening, event('SELL',100,'50','5'),
              event('BUY',200,'10','5'), event('SELL',100,'10.05','5'),
              event('SELL',100,'11','5')]
    rate = realized_sell_win_rate(events)
    assert rate['win_rate_pct'] == 50  # First apparent price gain loses after fees.
    assert rate['eligible_sell_orders'] == 2
    assert rate['excluded_opening_position_sell_orders'] == 1
