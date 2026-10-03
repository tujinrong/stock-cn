"""Cash-dividend receivable valuation for a single locked historical decision.

This is an outcome-only adapter. It does not supply future disclosures to the AI,
change execution cash, implement continuous dividend accounting, or settle tax.
Unsupported/unverified provider action hints fail closed for held securities.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse

from .sim_data import number


def validate_cash_dividends(data):
    policy = data.get('point_dividend_policy')
    events = data.get('verified_cash_dividends', [])
    if not policy and not events:
        return []
    if not isinstance(policy, dict) or policy.get('scope') != 'LOCKED_POINT_OUTCOME_ONLY':
        raise ValueError('cash dividends require an explicit point valuation policy')
    reserve = number(policy.get('tax_reserve_rate'))
    if not 0 <= reserve <= 1:
        raise ValueError('invalid dividend tax reserve assumption')
    if policy.get('income_basis') != 'EX_DATE_RECEIVABLE_WITH_TAX_RESERVE':
        raise ValueError('unsupported dividend valuation basis')
    if not isinstance(events, list):
        raise ValueError('cash dividend records must be a list')
    seen = set()
    for event in events:
        if event.get('kind') != 'VERIFIED_CASH_DIVIDEND' or event.get('official_source') is not True:
            raise ValueError('unverified or unsupported corporate action')
        symbol = event.get('symbol')
        if symbol not in data['instruments']:
            raise ValueError('dividend symbol outside supplied instruments')
        record, ex, payment = (date.fromisoformat(event[k]) for k in ('record_date', 'ex_date', 'payment_date'))
        published = datetime.fromisoformat(event['published_at'])
        if published.tzinfo is None or published.date() > record or not record < ex <= payment:
            raise ValueError('invalid cash dividend event timing')
        if number(event.get('cash_per_share_cny')) <= 0:
            raise ValueError('cash dividend must be positive')
        if event.get('share_change') != 'NONE':
            raise ValueError('share changes require a separate verified processor')
        host = urlparse(event.get('source_url', '')).hostname or ''
        if not any(host == d or host.endswith('.' + d) for d in ('cninfo.com.cn', 'sse.com.cn', 'szse.cn')):
            raise ValueError('dividend source must be a primary exchange disclosure')
        key = (symbol, event['ex_date'])
        if key in seen:
            raise ValueError('duplicate cash dividend entitlement')
        seen.add(key)
    return events


def unresolved_actions(data, symbols, start_date, end_date):
    """Return held-symbol hints which cannot be matched to a verified cash event."""
    events = {(e['symbol'], e['ex_date']): e for e in validate_cash_dividends(data)}
    gaps = []
    for day in data['sessions']:
        if not start_date < day <= end_date:
            continue
        for symbol in symbols:
            for hint in data['bars'].get(day, {}).get(symbol, {}).get('corporate_action_hints', []):
                event = events.get((symbol, hint.get('cqr') or day))
                matched = False
                if event is not None and hint.get('djr') == event['record_date']:
                    try:
                        # Tencent sometimes truncates the per-10-share figure.
                        # The official precise amount always determines the credit.
                        matched = abs(number(hint.get('fh_sh')) / 10 - number(event['cash_per_share_cny'])) <= Decimal('0.0001')
                    except (ValueError, TypeError):
                        pass
                    # Cash-only events cannot excuse a concurrent bonus or split.
                    content = hint.get('FHcontent', '')
                    if not isinstance(content, str) or '派' not in content or any(w in content for w in ('送', '转', '配')):
                        matched = False
                if not matched:
                    gaps.append({'symbol': symbol, 'date': day, 'status': 'UNVERIFIED_OR_UNSUPPORTED_CORPORATE_ACTION'})
    return gaps


def dividend_entitlements(state, opening, data, *, start_date, execution_date, day):
    """Add net receivables at ex-date; payment changes liquidity, not total wealth.

    The account has exactly one possible trade at execution_date, then is held.
    A purchase on ex-date has no entitlement; a sale on ex-date retains the
    entitlement established at the prior record-date. The tax reserve is a
    frozen experimental assumption, never a claim about actual personal tax.
    """
    events = validate_cash_dividends(data)
    reserve = number((data.get('point_dividend_policy') or {}).get('tax_reserve_rate', 0))
    out = []
    for event in events:
        if not start_date < event['ex_date'] <= day:
            continue
        record_state = opening if event['record_date'] < execution_date else state
        quantity = sum(p['quantity'] for p in record_state['positions'] if p['symbol'] == event['symbol'])
        if not quantity:
            continue
        gross = (Decimal(quantity) * number(event['cash_per_share_cny'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        tax = (gross * reserve).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        out.append({**event, 'eligible_quantity': quantity,
                    'gross_dividend_cny': str(gross), 'tax_reserve_cny': str(tax),
                    'net_dividend_cny': str(gross - tax),
                    'valuation_status': 'PAID' if event['payment_date'] <= day else 'RECEIVABLE'})
    return out


def point_valuation(state, opening, data, day, *, start_date, execution_date):
    value = number(state['cash_cny'])
    for p in state['positions']:
        value += Decimal(p['quantity']) * number(data['bars'][day][p['symbol']]['close'])
    return value + sum((number(e['net_dividend_cny']) for e in dividend_entitlements(
        state, opening, data, start_date=start_date, execution_date=execution_date, day=day)), Decimal(0))
