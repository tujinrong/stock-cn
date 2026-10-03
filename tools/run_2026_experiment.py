"""2026 A-E point-case comparison using archived public inputs outside the repo."""
import argparse
import copy
import json
from pathlib import Path

from stock_cn.experiments import ae_variants, freeze_experiment, require_all_decisions_locked, compare_experiment
from stock_cn.evaluation import prepare_batch, score_locked_decision, summarize
from stock_cn.simulation import Store, read_json, require, digest
from stock_cn.sim_cli import formal_fingerprints
from stock_cn.sim_data import source_corporate_action_hints


EID = 'ae-2026-v3'
DATES = ['2026-01-09', '2026-04-30', '2026-07-31']
POLICY = {'scope': 'LOCKED_POINT_OUTCOME_ONLY', 'income_basis': 'EX_DATE_RECEIVABLE_WITH_TAX_RESERVE',
          'tax_reserve_rate': '0.20', 'note': 'Uniform conservative experimental reserve; not actual personal tax settlement.'}
FIXED = ['600036.SH', '002594.SZ', '600660.SH', '600900.SH', '601100.SH']
RESEARCH = ['600036.SH', '600519.SH', '600276.SH', '600900.SH', '600660.SH',
            '600309.SH', '601318.SH', '601088.SH', '600028.SH', '601006.SH']


def enrich(data, hints):
    for result in hints['results']:
        for event in result.get('event_metadata', []):
            row = [event['row_date'], None, None, None, None, None, event['metadata']]
            data['bars'][event['row_date']][result['symbol']]['corporate_action_hints'] = source_corporate_action_hints(
                row, result['provider'], result['source'])
    data['point_dividend_policy'] = copy.deepcopy(POLICY)
    data['prompt_payload_codec'] = True
    data['research_namespace'] = EID
    data['evaluation_start_known'] = None
    data['limitations'].append('Source action hints are unverified. Only post-lock official cash dividend records may resolve scoring gaps.')
    return data


def research_inputs(repo, variant, target, facts, *, write=True):
    symbols = FIXED if variant[0] in 'AC' else RESEARCH
    reviews = {}
    withheld = []
    for s in symbols:
        review = copy.deepcopy(facts['by_target_date'][target][s])
        if review.get('source_publication_precision', '').startswith('DATE_ONLY') and review['source_published_at'][:10] >= target:
            withheld.append({'symbol': s, 'reason': 'DATE_ONLY_REPORT_NOT_PROVEN_AVAILABLE_BEFORE_CLOSE'})
        else:
            reviews[s] = review
    for review in reviews.values():
        # Reconstruction time is audit metadata, not historical decision evidence.
        review.pop('historical_review_performed_at', None)
        review['review_type'] = 'RECONSTRUCTED_FROM_CAUSAL_OFFICIAL_REPORT'
    reports = [{
        'symbol': s, 'title': r['source_report_title'], 'published_at': r['source_published_at'],
        'source_official': True, 'source_provider': 'CNINFO', 'document_url': r['source_report'],
        'is_periodic_report_body': True, 'category': 'PERIODIC_REPORT',
        'document_sha256': r.get('source_report_sha256'),
    } for s, r in reviews.items()]
    store = Store(repo / 'research-inputs' / EID / variant / target)
    payloads = {}
    payloads['manifest.json'] = {'variant_id': variant, 'mode': 'SIMULATION', 'decision_date': target,
        'information_cutoff': target + 'T15:00:00+08:00', 'source_commit': None, 'formal_execution': False,
        'research_method': 'PUBLIC_ARCHIVE_RECONSTRUCTION; only report facts published by cutoff',
        'shared_research_origin': 'Official archive reviews; date-only reports on target day withheld',
        'withheld_sources': withheld}
    payloads['financial-reviews.json'] = reviews
    payloads['official-disclosure-pack.json'] = {
        'kind': 'OFFICIAL_DISCLOSURE_PACK', 'symbols_requested': symbols,
        'results': [{'symbol': s, 'provider_status': 'OK' if s in reviews else 'FAILED',
                     'items': [r for r in reports if r['symbol'] == s],
                     'error': None if s in reviews else 'Publication time before historical close not proven'} for s in symbols],
        'latest_periodic_report_refs': reports, 'important_recent_refs': [],
        'withheld_sources': withheld,
        'coverage_note': 'Latest report metadata checked against public archive; same-day date-only sources withheld, not all litigation/media events reviewed.'}
    payloads['news-research.json'] = {'status': 'NOT_CHECKED', 'items': []}
    payloads['universe-scope.json'] = {'authorized_symbols': symbols, 'coverage': 'PREDECLARED_FIXED_RESEARCH_UNIVERSE',
                                      'not_full_a_share_claim': True}
    if variant[0] in 'DE':
        payloads['candidate-research-pack.json'] = {'kind': 'AI_SELECT_DEEP_RESEARCH_PACK',
            'purpose': 'LOW_RECOVERY' if variant[0] == 'D' else 'EARNINGS_IMPROVEMENT',
            'cutoff_date': target, 'selected_count': len(symbols), 'not_a_recommendation': True,
            'candidates': [{'symbol': s, 'name': None} for s in symbols],
            'coverage_note': 'Same ten-stock declared universe as earlier pilot; candidates are research scope, not winners.'}
    for name, value in payloads.items():
        require(not store.path(name).exists() or read_json(store.path(name)) == value,
                'experiment research source changed; use a new experiment_id')
    if write:
        for name, value in payloads.items():
            if not store.path(name).exists():
                store.write(name, value)
    return payloads


def prepare(repo, args):
    experiment_store = Store(repo / 'runs/experiments' / EID)
    require(not any(any((repo / 'runs/evaluations' / (EID + '-' + arm) / 'decisions').glob('*/*.json'))
                    for arm in ('baseline', 'candidate')),
            'experiment decisions exist; cannot prepare or overwrite research sources')
    data = enrich(read_json(args.data), read_json(args.rights))
    facts = read_json(args.facts)
    identity = {'facts_sha256': digest(facts), 'research_namespace': EID, 'point_dividend_policy': POLICY}
    identity_path = experiment_store.path('input-identity.json')
    if identity_path.exists():
        require(read_json(identity_path) == identity, 'experiment research input identity changed')
    audit_path = experiment_store.path('research-audit.json')
    if audit_path.exists():
        require(read_json(audit_path)['facts_sha256'] == identity['facts_sha256'], 'experiment financial facts changed')
    if not identity_path.exists():
        experiment_store.write('input-identity.json', identity)
    variants = ae_variants(repo)
    require(all(day in data['sessions'] for day in DATES), 'missing declared 2026 decision date')
    targets = []
    for i, day in enumerate(DATES):
        index = data['sessions'].index(day)
        require(index + 41 < len(data['sessions']), 'incomplete declared 41-session capital interval')
        targets.append({'date': day, 'phase': 'DEVELOPMENT' if i == 0 else 'HOLDOUT',
                        'capital_interval_end': data['sessions'][index + 41]})
    require(all(a['capital_interval_end'] < b['date'] for a, b in zip(targets, targets[1:])),
            'development and holdout capital windows overlap')
    plan = {'variants': variants, 'targets': targets, 'horizon_sessions': 40,
        'elapsed_capital_sessions': 41, 'data_year': 2026, 'actual_history_end': data['sessions'][-1],
        'max_input_chars': 120000, 'max_ai_decisions': 72, 'prompt_rendering': 'LOSSLESS_SHARED_JSON',
        'fixed_symbols': FIXED, 'research_symbols': RESEARCH, 'point_dividend_policy': POLICY,
        'initial_capital_per_variant_cny': '200000', 'objective': 'ISOLATED_RETURN_COMPARISON',
        'user_authorization': '用2026年数据，把A-E所有变体进行测试，并改进，提高收益率。',
        'candidate_rule': 'One frozen capital/holding opportunity-cost review; immutable strategy unchanged.',
        'evaluation_rule': 'Positive mean heldout net return difference with no worse daily drawdown in either holdout.',
        'same_day_date_only_report_policy': 'WITHHOLD_UNTIL_NEXT_CALENDAR_DAY',
        'no_automatic_formal_or_default_simulation_promotion': True,
        'B': {'status': 'RESERVED', 'variants': [], 'not_tested_reason': 'No strategy/account exists; no invented B variants.'}}
    before = formal_fingerprints(repo)
    manifest = freeze_experiment(repo, EID, plan)
    # Check every prior research file before writing any source in this batch.
    for v in variants:
        for target in DATES:
            research_inputs(repo, v, target, facts, write=False)
    for v in variants:
        for target in DATES:
            research_inputs(repo, v, target, facts)
    sizes = []
    for arm in ('baseline', 'candidate'):
        prepared = prepare_batch(repo, EID + '-' + arm, variants, data, DATES,
                                 prompt_selections=manifest['prompt_selections'][arm])
        for entry in prepared['entries']:
            size = len((repo / entry['ai_input_path']).read_text(encoding='utf-8'))
            require(size <= plan['max_input_chars'], 'complete input exceeds declared budget; do not truncate')
            sizes.append(size)
    require(before == formal_fingerprints(repo), 'formal files changed during preparation')
    store = Store(repo / 'runs/experiments' / EID)
    store.write('source-coverage.json', read_json(args.coverage))
    store.write('official-actions-audit.json', read_json(args.actions))
    store.write('research-audit.json', {'method': '36 reconstructed reviews from official archived report bodies; 2 unique same-day date-only sources withheld',
        'raw_data_outside_repository': True, 'raw_reports_outside_repository': True,
        'facts_sha256': digest(facts), 'no_future_prices_used_by_researchers': True,
        'formal_files_unchanged': True, 'actual_ai_decisions_pending': 72})
    store.write('preparation-validation.json', {'status': 'READY_FOR_AI', 'complete_inputs': 72,
        'min_input_chars': min(sizes), 'max_input_chars': max(sizes), 'declared_input_limit': 120000,
        'lossless_codec_roundtrip_tested': True, 'predecessor': 'ae-2026-v2', 'actual_ai_decisions': 0})
    print(json.dumps({'experiment_id': EID, 'variants': len(variants), 'decision_requests': 72, 'targets': targets}, ensure_ascii=False))


def score(repo, args):
    manifest = read_json(repo / 'runs/experiments' / EID / 'manifest.json')
    require_all_decisions_locked(repo, manifest)  # before reading any outcome price/event input
    before = formal_fingerprints(repo)
    data = enrich(read_json(args.data), read_json(args.rights))
    actions = read_json(args.actions)
    data['verified_cash_dividends'] = [{
        'kind': 'VERIFIED_CASH_DIVIDEND', 'symbol': e['symbol'], 'published_at': e['published_at'],
        'record_date': e['record_date'], 'ex_date': e['ex_date'], 'payment_date': e['payment_date'],
        'cash_per_share_cny': e['cash_per_share'], 'official_source': e['source_official'],
        'share_change': 'NONE' if e['cash_only'] and e['stock_dividend_ratio'] == e['capitalization_ratio'] == '0' else 'UNSUPPORTED',
        'source_url': e['source'], 'verification': e['verification'],
    } for e in actions['events']]
    for arm in ('baseline', 'candidate'):
        eid = EID + '-' + arm
        for v in manifest['plan']['variants']:
            for target in manifest['plan']['targets']:
                score_locked_decision(repo, eid, v, target['date'], data, (40,))
        summarize(repo, eid)
    require(before == formal_fingerprints(repo), 'formal files changed during scoring')
    result = compare_experiment(repo, manifest)
    print(json.dumps(result['variant_summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', default='.')
    p.add_argument('--phase', choices=['prepare', 'score'], required=True)
    for field in ('data', 'facts', 'rights', 'actions', 'coverage'):
        p.add_argument('--' + field, required=field != 'facts')
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    if args.phase == 'prepare':
        require(args.facts, 'preparation requires official financial facts')
        prepare(repo, args)
    else:
        score(repo, args)
