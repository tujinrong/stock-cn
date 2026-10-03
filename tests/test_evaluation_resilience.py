import copy
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from test_simulation import repo
from test_evaluation import history, make_buy_decision
from stock_cn.evaluation import prepare_batch, save_locked_decision, score_locked_decision
from stock_cn.simulation import Store, read_json, ValidationError
from stock_cn.variant_prompts import materialize


def prepared(repo, eid='resilient', days=70):
    materialize(repo)
    data = history(days=days)
    target = data['sessions'][8]
    entry = prepare_batch(repo, eid, ['C02'], data, [target])['entries'][0]
    decision, request = make_buy_decision(repo, eid, 'C02', target)
    save_locked_decision(repo, eid, 'C02', target, decision)
    store = Store((repo / entry['request_path']).parent.parent.parent)
    return data, target, entry, store


@pytest.mark.parametrize('artifact', ['request_path', 'time_travel_path', 'ai_input_path'])
def test_changed_prepared_inputs_cannot_be_sealed(repo, artifact):
    materialize(repo)
    data = history()
    target = data['sessions'][8]
    entry = prepare_batch(repo, 'before-lock', ['C02'], data, [target])['entries'][0]
    decision, _ = make_buy_decision(repo, 'before-lock', 'C02', target)
    path = repo / entry[artifact]
    if artifact == 'ai_input_path':
        path.write_text('changed saved AI input', encoding='utf-8')
    else:
        document = read_json(path)
        if artifact == 'request_path':
            document['holdings']['cash_cny'] = '999999.00'
        else:
            document['symbols'][0]['as_of_close'] = '1.00'
        Store(path.parent).write(path.name, document)
    with pytest.raises(ValidationError, match='changed'):
        save_locked_decision(repo, 'before-lock', 'C02', target, decision)
    assert not (repo / entry['decision_path']).exists()


def test_repeat_and_extension_preserve_execution_and_original_fee_schedule(repo):
    data, target, entry, store = prepared(repo, days=30)
    first = score_locked_decision(repo, 'resilient', 'C02', target, data)
    assert first['scores'][-1]['status'] == 'INSUFFICIENT_FUTURE_SESSIONS'
    old_events = copy.deepcopy(store.events())
    Store(repo).write('config/default.json', {'min_commission': '1000'})
    second = score_locked_decision(repo, 'resilient', 'C02', target, history(days=70))
    assert second['scores'][0] == first['scores'][0]
    assert second['scores'][-1]['status'] == 'SCORED'
    assert store.events() == old_events
    subset = score_locked_decision(repo, 'resilient', 'C02', target, history(days=70), (5,))
    assert len(subset['scores']) == 3
    assert subset['execution'] == first['execution']


@pytest.mark.parametrize('crash_at', ['projection', 'score'])
def test_crash_after_durable_execution_recovers_without_duplicate_fill(repo, monkeypatch, crash_at):
    data, target, entry, store = prepared(repo)
    original_project, original_write = Store.project, Store.write
    fired = False
    def project(self, event):
        nonlocal fired
        if crash_at == 'projection' and event['type'] == 'DAY_COMPLETED' and not fired:
            fired = True
            raise OSError('injected projection crash')
        return original_project(self, event)
    def write(self, name, value):
        nonlocal fired
        if crash_at == 'score' and name.startswith('scores/') and not fired:
            fired = True
            raise OSError('injected score crash')
        return original_write(self, name, value)
    monkeypatch.setattr(Store, 'project', project)
    monkeypatch.setattr(Store, 'write', write)
    with pytest.raises(OSError, match='injected'):
        score_locked_decision(repo, 'resilient', 'C02', target, data)
    assert len(store.events()) == 2
    result = score_locked_decision(repo, 'resilient', 'C02', target, data)
    assert result['execution']['status'] == 'FILLED'
    assert len(store.events()) == 2 and store.audit()['ok']


def test_concurrent_scoring_has_one_writer(repo, monkeypatch):
    data, target, entry, store = prepared(repo)
    entered, release = Event(), Event()
    original = Store.commit
    def delayed(self, event_type, *args, **kwargs):
        if event_type == 'DAY_COMPLETED':
            entered.set()
            assert release.wait(10)
        return original(self, event_type, *args, **kwargs)
    monkeypatch.setattr(Store, 'commit', delayed)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(score_locked_decision, repo, 'resilient', 'C02', target, data)
        assert entered.wait(10)
        try:
            with pytest.raises(ValidationError, match='busy'):
                score_locked_decision(repo, 'resilient', 'C02', target, data)
        finally:
            release.set()
        assert first.result()['execution']['status'] == 'FILLED'
    assert len(store.events()) == 2


def test_locked_request_fields_cannot_be_changed_or_regenerated(repo):
    data, target, entry, store = prepared(repo)
    with pytest.raises(ValidationError, match='already locked'):
        prepare_batch(repo, 'resilient', ['C02'], data, [target])
    request = read_json(repo / entry['request_path'])
    request['holdings']['cash_cny'] = '999999.00'
    store.write(f"requests/{entry['execution_date']}/request.json", request)
    with pytest.raises(ValidationError, match='request changed'):
        score_locked_decision(repo, 'resilient', 'C02', target, data)
    assert len(store.events()) == 1


@pytest.mark.parametrize('changed_day', ['execution', 'outcome'])
def test_changed_execution_or_scored_outcome_does_not_rewrite_history(repo, changed_day):
    data, target, entry, store = prepared(repo)
    score_locked_decision(repo, 'resilient', 'C02', target, data)
    old_events = copy.deepcopy(store.events())
    score_path = repo / entry['score_path']
    old_score = score_path.read_bytes()
    changed = copy.deepcopy(data)
    day = entry['execution_date'] if changed_day == 'execution' else data['sessions'][14]
    key = 'open' if changed_day == 'execution' else 'close'
    changed['bars'][day]['600036.SH'][key] = '41.90' if changed_day == 'execution' else '42.90'
    with pytest.raises(ValidationError, match='differs|changed'):
        score_locked_decision(repo, 'resilient', 'C02', target, changed)
    assert store.events() == old_events and score_path.read_bytes() == old_score
