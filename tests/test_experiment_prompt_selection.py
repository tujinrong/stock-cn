"""Isolated prompt experiments and complete decision sealing before outcomes."""
import importlib.util
from pathlib import Path

import pytest

from test_simulation import repo
from test_evaluation import history, make_buy_decision
from stock_cn.evaluation import prepare_batch, save_locked_decision, score_locked_decision
from stock_cn.sim_cli import formal_fingerprints
from stock_cn.sim_data import fixture
from stock_cn.sim_variants import VariantSimulation
from stock_cn.simulation import ValidationError, digest, read_json
from stock_cn.variant_prompts import materialize, write


@pytest.fixture
def candidate(repo):
    materialize(repo)
    root = repo / 'strategies/C/variants/C02'
    text = (root / 'prompt_versions/v000.md').read_text(encoding='utf-8')
    text += '\nEXPERIMENT_ONLY: Explain uncertainty using supplied causal evidence.\n'
    write(root / 'experiment-prompts/candidate.md', text)
    return {'version': 'exp-2026-v1', 'path': 'experiment-prompts/candidate.md',
            'sha256': digest(text)}


def test_candidate_and_baseline_are_isolated_without_pointer_changes(repo, candidate):
    root = repo / 'strategies/C/variants/C02'
    before = formal_fingerprints(repo)
    pointer_before = (root / 'simulation_prompt.json').read_bytes()
    baseline = VariantSimulation(repo, 'C', 'C02', 'baseline', fixture())
    experiment = VariantSimulation(repo, 'C', 'C02', 'candidate', fixture(),
                                   prompt_selection=candidate)
    baseline_request = baseline.prepare('2025-08-04')
    candidate_request = experiment.prepare('2025-08-04')
    assert 'EXPERIMENT_ONLY' not in baseline_request['prompt']
    assert 'EXPERIMENT_ONLY' in candidate_request['prompt']
    assert baseline.store.root != experiment.store.root
    assert baseline.store.load()['total_equity_cny'] == experiment.store.load()['total_equity_cny']
    assert experiment.prompt_selection == candidate
    assert formal_fingerprints(repo) == before
    assert (root / 'simulation_prompt.json').read_bytes() == pointer_before
    with pytest.raises(ValidationError, match='inputs changed'):
        VariantSimulation(repo, 'C', 'C02', 'baseline', fixture(),
                          prompt_selection=candidate).initialize()


@pytest.mark.parametrize('field,value,message', [
    ('version', '../v1', 'version'),
    ('version', None, 'version'),
    ('path', '../C01/prompt.md', 'path escape'),
    ('path', '', 'path must be relative'),
    ('sha256', 'bad', 'selection hash'),
    ('sha256', '0' * 64, 'hash mismatch'),
])
def test_explicit_selection_rejects_invalid_identity_path_and_hash(repo, candidate, field, value, message):
    selection = {**candidate, field: value}
    with pytest.raises(ValidationError, match=message):
        VariantSimulation(repo, 'C', 'C02', 'bad-selection', fixture(),
                          prompt_selection=selection)
    assert not (repo / 'strategies/C/variants/C02/simulations/bad-selection').exists()


def test_absolute_or_changed_strategy_prompt_cannot_be_selected(repo, candidate):
    root = repo / 'strategies/C/variants/C02'
    with pytest.raises(ValidationError, match='path must be relative'):
        VariantSimulation(repo, 'C', 'C02', 'absolute', fixture(),
                          prompt_selection={**candidate, 'path': str(root / candidate['path'])})
    file = root / candidate['path']
    changed = file.read_text(encoding='utf-8').replace('initial_capital_cny": 200000',
                                                    'initial_capital_cny": 300000')
    write(file, changed)
    with pytest.raises(ValueError, match='investment intent'):
        VariantSimulation(repo, 'C', 'C02', 'changed-intent', fixture(),
                          prompt_selection={**candidate, 'sha256': digest(changed)})


def test_evaluation_keeps_exact_selection_after_global_pointer_changes(repo, candidate):
    data = history()
    target = data['sessions'][8]
    before = formal_fingerprints(repo)
    entry = prepare_batch(repo, 'candidate-eval', ['C02'], data, [target],
                          prompt_selections={'C02': candidate})['entries'][0]
    assert entry['prompt_selection'] == candidate
    decision, _ = make_buy_decision(repo, 'candidate-eval', 'C02', target)
    save_locked_decision(repo, 'candidate-eval', 'C02', target, decision)
    root = repo / 'strategies/C/variants/C02'
    # A later default selection must not change the already sealed experiment.
    write(root / 'simulation_prompt.json', {'version': 'v999', 'path': 'missing.md',
                                           'sha256': '0' * 64})
    result = score_locked_decision(repo, 'candidate-eval', 'C02', target, data, (5,))
    assert result['scores'][0]['status'] == 'SCORED'
    assert formal_fingerprints(repo) == before
    entry['prompt_selection']['version'] = 'changed-after-lock'
    write(repo / 'runs/evaluations/candidate-eval/entries/C02' / f'{target}.json', entry)
    with pytest.raises(ValidationError, match='entry changed after decision lock'):
        score_locked_decision(repo, 'candidate-eval', 'C02', target, data, (5,))


def test_unknown_variant_selector_is_rejected_before_preparation(repo, candidate):
    data = history()
    with pytest.raises(ValidationError, match='planned variants'):
        prepare_batch(repo, 'foreign', ['A01'], data, [data['sessions'][8]],
                      prompt_selections={'C02': candidate})
    assert not (repo / 'runs/evaluations/foreign').exists()


@pytest.fixture
def plan_tool():
    path = Path(__file__).resolve().parents[1] / 'tools/run_evaluation_plan.py'
    spec = importlib.util.spec_from_file_location('experiment_evaluation_plan', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepared_plan(repo):
    materialize(repo)
    data = history()
    target = data['sessions'][8]
    plan = {'eval_id': 'whole-batch', 'variants': ['C01', 'C02'],
            'target_dates': [target], 'score_horizons': [5]}
    prepare_batch(repo, plan['eval_id'], plan['variants'], data, plan['target_dates'])
    for variant in plan['variants']:
        decision, _ = make_buy_decision(repo, plan['eval_id'], variant, target)
        write(repo / 'evaluation-answers' / plan['eval_id'] / variant / f'{target}.json', decision)
    return plan, data, target


def test_missing_planned_answer_refuses_partial_lock_and_never_fetches(repo, plan_tool, monkeypatch):
    plan, _, target = prepared_plan(repo)
    (repo / 'evaluation-answers/whole-batch/C02' / f'{target}.json').unlink()
    def forbidden_fetch(plan):
        pytest.fail('future prices acquired before complete answers')
    monkeypatch.setattr(plan_tool, 'fetch', forbidden_fetch)
    with pytest.raises(ValidationError, match='planned answer missing: C02'):
        plan_tool.score(repo, plan)
    assert not (repo / 'runs/evaluations/whole-batch/decisions').exists()


def test_all_decisions_are_sealed_before_future_data_and_locked_rerun_needs_no_answers(repo, plan_tool, monkeypatch):
    plan, data, target = prepared_plan(repo)
    fetched = []
    def checked_fetch(actual_plan):
        for variant in actual_plan['variants']:
            p = repo / 'runs/evaluations/whole-batch/decisions' / variant / f'{target}.lock.json'
            lock = read_json(p)
            assert lock['locked'] is True
            assert lock['future_outcomes_seen_by_decision_phase'] is False
        fetched.append(True)
        return data, []
    monkeypatch.setattr(plan_tool, 'fetch', checked_fetch)
    summary = plan_tool.score(repo, plan)
    assert summary['scored_entries'] == 2
    for variant in plan['variants']:
        (repo / 'evaluation-answers/whole-batch' / variant / f'{target}.json').unlink()
    repeated = plan_tool.score(repo, plan)
    assert repeated == summary and len(fetched) == 2
    for variant in plan['variants']:
        events = repo / f'strategies/C/variants/{variant}/simulations/eval-whole-batch-{target.replace("-", "")}/events'
        assert len(list(events.glob('*.json'))) == 2


def test_invalid_late_decision_never_acquires_future_prices(repo, plan_tool, monkeypatch):
    plan, _, target = prepared_plan(repo)
    path = repo / 'evaluation-answers/whole-batch/C02' / f'{target}.json'
    answer = read_json(path)
    answer['input_revision'] += 1
    write(path, answer)
    monkeypatch.setattr(plan_tool, 'fetch', lambda plan: pytest.fail('unsealed batch acquired future prices'))
    with pytest.raises(ValidationError, match='identity mismatch'):
        plan_tool.score(repo, plan)
    assert not (repo / 'runs/evaluations/whole-batch/scores').exists()
