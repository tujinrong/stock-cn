"""Serialize explicit AI choices against saved causal requests, then seal them.

No strategy is implemented here. The caller supplies action/status/quantity,
reason, risks, gaps and evidence symbols; only identity and quotes are copied.
This phase never opens an outcome market-data file.
"""
import argparse
from pathlib import Path

from stock_cn.simulation import read_json, Store, require, digest
from stock_cn.sim_agents import decision_base
from stock_cn.paper_core import validate_decision_contract
from stock_cn.research_bundle import buy_research_preflight
from stock_cn.evaluation import save_locked_decision


def lock_choices(repo, experiment_id, choices):
    manifest = read_json(repo / 'runs/experiments' / experiment_id / 'manifest.json')
    valid_dates = {x['date'] for x in manifest['plan']['targets']}
    seen = set()
    for choice in choices:
        arm, variant, target = (choice[k] for k in ('arm', 'variant', 'target_date'))
        require(arm in {'baseline', 'candidate'} and variant in manifest['plan']['variants'] and target in valid_dates,
                'choice outside declared experiment')
        key = (arm, variant, target)
        require(key not in seen, 'duplicate AI choice')
        seen.add(key)
        eid = experiment_id + '-' + arm
        entry = read_json(repo / f'runs/evaluations/{eid}/entries/{variant}/{target}.json')
        request = read_json(repo / entry['request_path'])
        response = decision_base(request)
        response.update(status=choice['status'], action=choice.get('action'), summary=choice['summary'],
                        risks=choice['risks'], data_gaps=choice['data_gaps'])
        for symbol in choice.get('evidence_symbols', []):
            row = next(x for x in request['decision_research_bundle']['per_symbol'] if x['symbol'] == symbol)
            review = row['financial_review']
            require(isinstance(review, dict), 'cannot cite a missing financial review; record it as a data gap')
            response['evidence'].append({'source': review['source_report'], 'published_at': review['source_published_at'],
                'kind': 'OFFICIAL_REPORT_REVIEW', 'symbol': symbol,
                'facts_referenced': choice.get('facts_referenced', [])})
        response['evidence'].append({'source': 'SAVED_POINT_IN_TIME_PRICE_CONTEXT',
            'published_at': request['context']['information_cutoff'], 'kind': 'ARCHIVED_OHLCV'})
        if response['status'] == 'READY':
            if response['action'] != 'HOLD':
                symbol, quantity = choice['symbol'], choice['quantity']
                row = request['market'][symbol][-1]
                require(type(quantity) is int and quantity > 0 and quantity % 100 == 0, 'order lot invalid')
                response['order_proposal'] = {'symbol': symbol, 'side': response['action'], 'quantity': quantity,
                    'reference_price_cny': row['close'], 'quote_source': row['source'],
                    'quote_time': request['context']['information_cutoff']}
                if response['action'] == 'BUY':
                    require(buy_research_preflight(request['decision_research_bundle'], symbol)['ready'], 'BUY research missing')
            def check_symbol(symbol):
                require(symbol in request['market'], 'symbol outside causal request scope')
            validate_decision_contract(response, request, check_symbol)
        else:
            require(response['action'] is None, 'unavailable choice must have no action')
        decision = repo / entry['decision_path']
        if decision.exists():
            require(read_json(decision) == response, 'AI choice changed after sealing')
            lock = read_json(decision.with_suffix('.lock.json'))
            require(lock.get('locked') is True and lock.get('decision_sha256') == digest(response),
                    'existing AI decision is not sealed')
        else:
            save_locked_decision(repo, eid, variant, target, response)
        Store(repo / 'evaluation-answers' / eid).write(f'{variant}/{target}.json', response)
    return len(seen)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', default='.')
    p.add_argument('--experiment-id', required=True)
    p.add_argument('--choices', required=True)
    args = p.parse_args()
    print(f"{lock_choices(Path(args.repo).resolve(), args.experiment_id, read_json(args.choices))} AI choices sealed; no outcome file opened")
