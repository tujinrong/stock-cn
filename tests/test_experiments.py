import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_simulation import repo
from stock_cn.experiments import freeze_experiment, ae_variants, require_all_decisions_locked
from stock_cn.variant_prompts import materialize
from stock_cn.simulation import Store, read_json, ValidationError
from stock_cn.sim_cli import formal_fingerprints
from stock_cn.research_bundle import validate_financial_review
from test_research_bundle import financial_review
from test_evaluation import history
from stock_cn.evaluation import prepare_batch, save_locked_decision
from stock_cn.sim_agents import decision_base
from stock_cn.variant_prompts import variant_root
from test_research_inputs import official
from stock_cn.evidence import validate_official_disclosure_pack


def plan(repo):
    return {'variants': ae_variants(repo), 'objective': 'ISOLATED_RETURN_COMPARISON',
            'user_authorization': '2026 A-E isolated comparison and improvement',
            'targets': [{'date': '2026-01-09', 'phase': 'DEVELOPMENT'},
                        {'date': '2026-04-30', 'phase': 'HOLDOUT'}], 'horizon_sessions': 40}


def test_candidate_freeze_counts_once_and_does_not_switch_global_prompts(repo):
    materialize(repo)
    assert len(ae_variants(repo)) == 12 and not any(v.startswith('B') for v in ae_variants(repo))
    before = formal_fingerprints(repo)
    pointers = {v: read_json(repo / f'strategies/{v[0]}/variants/{v}/simulation_prompt.json') for v in ae_variants(repo)}
    frozen = freeze_experiment(repo, 'year-2026', plan(repo))
    assert freeze_experiment(repo, 'year-2026', plan(repo)) == frozen
    assert before == formal_fingerprints(repo)
    for v in ae_variants(repo):
        root = repo / f'strategies/{v[0]}/variants/{v}'
        assert read_json(root / 'improvement_state.json')['rounds_used'] == 1
        assert read_json(root / 'simulation_prompt.json') == pointers[v]
    changed = copy.deepcopy(plan(repo))
    changed['horizon_sessions'] = 20
    with pytest.raises(ValidationError, match='frozen experiment changed'):
        freeze_experiment(repo, 'year-2026', changed)
    with pytest.raises(FileNotFoundError):
        require_all_decisions_locked(repo, frozen)


def test_experiment_cannot_bypass_budget_or_use_seen_outcomes(repo):
    materialize(repo)
    Store(repo).write('runs/evaluations/late-candidate/scores/A01/2026-01-09.json', {'status': 'SCORED'})
    with pytest.raises(ValidationError, match='after seeing'):
        freeze_experiment(repo, 'late', plan(repo))
    root = repo / 'strategies/A/variants/A01'
    state = read_json(root / 'improvement_state.json')
    state['rounds_used'] = 10
    Store(root).write('improvement_state.json', state)
    with pytest.raises(ValidationError, match='budget'):
        freeze_experiment(repo, 'exhausted', plan(repo))


@pytest.mark.parametrize('field', ['source_published_at', 'fact'])
def test_financial_source_timestamps_cannot_bypass_review_as_of(field):
    review = financial_review()
    if field == 'source_published_at':
        review[field] = '2026-10-09T00:00:00+08:00'
    else:
        review['facts'][0]['published_at'] = '2026-10-09T00:00:00+08:00'
    with pytest.raises(ValueError, match='future financial'):
        validate_financial_review(review, symbol='600036.SH', as_of='2026-10-08T11:00:00+08:00')


def load_runner():
    path = Path(__file__).resolve().parents[1] / 'tools/run_2026_experiment.py'
    spec = importlib.util.spec_from_file_location('experiment_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_arm_gate_blocks_outcome_reads_and_rejects_changed_prompt(repo, monkeypatch):
    materialize(repo)
    data = history()
    frozen_plan = plan(repo)
    frozen_plan['targets'] = [{'date': data['sessions'][8], 'phase': 'DEVELOPMENT'},
                              {'date': data['sessions'][18], 'phase': 'HOLDOUT'}]
    runner = load_runner()
    manifest = freeze_experiment(repo, runner.EID, frozen_plan)
    for arm in ('baseline', 'candidate'):
        eid = runner.EID + '-' + arm
        entries = prepare_batch(repo, eid, frozen_plan['variants'], data,
            [x['date'] for x in frozen_plan['targets']],
            prompt_selections=manifest['prompt_selections'][arm])['entries']
        for entry in entries:
            request = read_json(repo / entry['request_path'])
            decision = decision_base(request)
            decision.update(status='INSUFFICIENT_DATA', action=None,
                            summary='TEST_ONLY incomplete research, not an investment result')
            save_locked_decision(repo, eid, entry['variant'], entry['target_date'], decision)
    assert require_all_decisions_locked(repo, manifest)
    last_lock = repo / entry['decision_path']
    last_lock = last_lock.with_suffix('.lock.json')
    last_lock.unlink()
    opened = []
    original_read = runner.read_json
    def tracked_read(path):
        opened.append(str(path))
        return original_read(path)
    monkeypatch.setattr(runner, 'read_json', tracked_read)
    args = SimpleNamespace(data='FORBIDDEN_FUTURE_PRICES', rights='FORBIDDEN_FUTURE_HINTS',
                           actions='FORBIDDEN_FUTURE_ACTIONS')
    with pytest.raises(FileNotFoundError):
        runner.score(repo, args)
    assert len(opened) == 1 and opened[0].endswith('manifest.json')
    selection = manifest['prompt_selections']['candidate']['A01']
    prompt = variant_root(repo, 'A01') / selection['path']
    prompt.write_text(prompt.read_text(encoding='utf-8') + '\nchanged', encoding='utf-8')
    with pytest.raises(ValidationError, match='strategy prompt changed'):
        require_all_decisions_locked(repo, manifest)


def test_date_only_report_cannot_be_assumed_public_at_midnight():
    cutoff = '2026-10-08T15:00:00+08:00'
    review = financial_review()
    review['source_published_at'] = '2026-10-08T00:00:00+08:00'
    review['source_publication_precision'] = 'DATE_ONLY_CNINFO_METADATA'
    with pytest.raises(ValueError, match='date-only financial'):
        validate_financial_review(review, symbol='600036.SH', as_of=cutoff)
    review['source_published_at'] = '2026-10-07T00:00:00+08:00'
    assert validate_financial_review(review, symbol='600036.SH', as_of=cutoff)
    review['source_publication_precision'] = 'EXACT_SOURCE_TIMESTAMP'
    review['source_published_at'] = '2026-10-08T14:00:00+08:00'
    assert validate_financial_review(review, symbol='600036.SH', as_of=cutoff)
    pack = official()
    report = pack['results'][0]['items'][0]
    report.update(published_at='2026-10-08T00:00:00+08:00', publication_precision='DATE_ONLY_CNINFO_METADATA')
    with pytest.raises(ValueError, match='date-only official'):
        validate_official_disclosure_pack(pack, as_of=cutoff)


def test_reprepare_cannot_overwrite_locked_research_before_failure(repo):
    runner = load_runner()
    Store(repo).write(f'runs/evaluations/{runner.EID}-baseline/decisions/A01/2026-01-09.json', {'locked': 'TEST'})
    with pytest.raises(ValidationError, match='cannot prepare or overwrite'):
        runner.prepare(repo, SimpleNamespace(data='DO_NOT_OPEN'))


def test_research_archive_rewrite_is_rejected_before_any_file_changes(repo):
    runner = load_runner()
    target = '2026-10-08'
    reviews = {}
    for symbol in runner.FIXED:
        review = financial_review()
        review.update(symbol=symbol, source_report_title='TEST_ONLY report',
                      source_published_at='2026-10-07T00:00:00+08:00')
        reviews[symbol] = review
    facts = {'by_target_date': {target: reviews}}
    original = runner.research_inputs(repo, 'C01', target, facts)
    changed = copy.deepcopy(facts)
    changed['by_target_date'][target][runner.FIXED[0]]['summary'] = 'changed after freezing'
    with pytest.raises(ValidationError, match='research source changed'):
        runner.research_inputs(repo, 'C01', target, changed)
    for name, value in original.items():
        assert read_json(repo / f'research-inputs/{runner.EID}/C01/{target}/{name}') == value
