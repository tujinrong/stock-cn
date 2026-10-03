import copy

import pytest

from test_simulation import repo
from test_evaluation import history, make_buy_decision
from stock_cn.evaluation import prepare_batch, save_locked_decision, score_locked_decision
from stock_cn.point_dividends import point_valuation, dividend_entitlements, unresolved_actions, validate_cash_dividends
from stock_cn.variant_prompts import materialize
from stock_cn.sim_variants import VariantSimulation
from stock_cn.sim_agents import decision_base
from stock_cn.sim_data import fixture


def data_with_dividend():
    data = history()
    data['point_dividend_policy'] = {'scope': 'LOCKED_POINT_OUTCOME_ONLY',
        'income_basis': 'EX_DATE_RECEIVABLE_WITH_TAX_RESERVE', 'tax_reserve_rate': '0.20'}
    data['verified_cash_dividends'] = [{'kind': 'VERIFIED_CASH_DIVIDEND', 'symbol': '600036.SH',
        'published_at': data['sessions'][2] + 'T00:00:00+08:00',
        'record_date': data['sessions'][12], 'ex_date': data['sessions'][13],
        'payment_date': data['sessions'][18], 'cash_per_share_cny': '1.00',
        'official_source': True, 'share_change': 'NONE',
        'source_url': 'https://static.cninfo.com.cn/finalpage/official.pdf'}]
    e = data['verified_cash_dividends'][0]
    data['bars'][e['ex_date']]['600036.SH']['corporate_action_hints'] = [{
        'djr': e['record_date'], 'cqr': e['ex_date'], 'fh_sh': '10', 'FHcontent': '10派10元'}]
    return data


def account(quantity):
    return {'cash_cny': '1000', 'positions': [{'symbol': '600036.SH', 'quantity': quantity}] if quantity else []}


@pytest.mark.parametrize('after_quantity', [0, 200])
def test_record_date_entitlement_survives_ex_date_sale_and_excludes_ex_date_buy(after_quantity):
    data = data_with_dividend()
    e = data['verified_cash_dividends'][0]
    before, after = account(100), account(after_quantity)
    income = dividend_entitlements(after, before, data, start_date=data['sessions'][8],
                                   execution_date=e['ex_date'], day=e['ex_date'])
    assert income[0]['eligible_quantity'] == 100
    assert income[0]['net_dividend_cny'] == '80.00'
    assert income[0]['valuation_status'] == 'RECEIVABLE'
    # Valuing a receivable must not fabricate spendable cash.
    assert after['cash_cny'] == '1000'
    paid = dividend_entitlements(after, before, data, start_date=data['sessions'][8],
                                 execution_date=e['ex_date'], day=e['payment_date'])
    assert paid[0]['valuation_status'] == 'PAID' and paid[0]['net_dividend_cny'] == '80.00'


def test_buy_on_record_date_has_entitlement_and_event_before_start_is_not_credited():
    data = data_with_dividend()
    e = data['verified_cash_dividends'][0]
    income = dividend_entitlements(account(100), account(0), data, start_date=data['sessions'][8],
                                   execution_date=e['record_date'], day=e['payment_date'])
    assert income[0]['net_dividend_cny'] == '80.00'
    assert not dividend_entitlements(account(100), account(100), data, start_date=e['ex_date'],
                                    execution_date=e['payment_date'], day=e['payment_date'])


def test_unverified_or_non_cash_hint_fails_closed_and_official_precision_is_retained():
    data = data_with_dividend()
    e = data['verified_cash_dividends'][0]
    args = (data, ['600036.SH'], data['sessions'][8], e['payment_date'])
    assert not unresolved_actions(*args)
    e['cash_per_share_cny'] = '1.00003'
    assert not unresolved_actions(*args)
    hint = data['bars'][e['ex_date']]['600036.SH']['corporate_action_hints'][0]
    hint['FHcontent'] = '10送5派10元'
    assert unresolved_actions(*args)
    hint['FHcontent'] = '10派10元'
    data['verified_cash_dividends'] = []
    assert unresolved_actions(*args)


@pytest.mark.parametrize('change', ['duplicate', 'future_publication', 'share_change', 'non_official_url'])
def test_invalid_dividend_records_are_rejected(change):
    data = data_with_dividend()
    e = data['verified_cash_dividends'][0]
    if change == 'duplicate':
        data['verified_cash_dividends'].append(copy.deepcopy(e))
    elif change == 'future_publication':
        e['published_at'] = e['ex_date'] + 'T00:00:00+08:00'
    elif change == 'share_change':
        e['share_change'] = 'BONUS'
    else:
        e['source_url'] = 'https://example.test/claims-official.pdf'
    with pytest.raises(ValueError):
        validate_cash_dividends(data)


def test_scoring_accounts_for_dividend_in_actual_and_hold_and_freezes_policy(repo):
    materialize(repo)
    data = data_with_dividend()
    target = data['sessions'][8]
    prepare_batch(repo, 'cash-dividend', ['C02'], data, [target])
    decision, request = make_buy_decision(repo, 'cash-dividend', 'C02', target)
    assert 'cash_per_share_cny' not in request['prompt']
    save_locked_decision(repo, 'cash-dividend', 'C02', target, decision)
    result = score_locked_decision(repo, 'cash-dividend', 'C02', target, data)
    scored = result['scores'][0]
    assert scored['dividend_entitlements'][0]['net_dividend_cny'] == '80.00'
    assert not scored['hold_dividend_entitlements']  # cash-only C opening benchmark
    assert scored['dividend_tax_reserve_cny'] == '20.00'
    changed = copy.deepcopy(data)
    changed['point_dividend_policy']['tax_reserve_rate'] = '0'
    with pytest.raises(ValueError, match='assumption changed'):
        score_locked_decision(repo, 'cash-dividend', 'C02', target, changed)
    unverified = copy.deepcopy(data)
    unverified['verified_cash_dividends'] = []
    with pytest.raises(ValueError, match='outcome changed'):
        score_locked_decision(repo, 'cash-dividend', 'C02', target, unverified)


def test_point_adapter_does_not_silently_enable_continuous_cash_account_events(repo):
    materialize(repo)
    data = fixture()
    day = data['sessions'][1]
    data['bars'][day]['600036.SH']['corporate_action_hints'] = [{'FHcontent': '10派10元'}]
    sim = VariantSimulation(repo, 'A', 'A01', 'cash-event-boundary', data)
    request = sim.prepare(day)
    decision = decision_base(request)
    decision['summary'] = 'TEST_ONLY HOLD with an unresolved action on a held stock'
    with pytest.raises(ValueError, match='verified continuous account processing'):
        sim.apply(day, decision)
    assert len(sim.store.events()) == 1
