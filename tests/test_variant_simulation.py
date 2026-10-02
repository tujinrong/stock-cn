import copy
import shutil
import pytest
from test_simulation import repo
from stock_cn.sim_data import fixture
from stock_cn.sim_agents import ScriptedSmokeAgent, decision_base
from stock_cn.simulation import read_json, ValidationError
from stock_cn.sim_variants import VariantSimulation, DecisionUnavailable
from stock_cn.variant_prompts import materialize, PromptLab, stable_patch


def make(repo, variant='A02', data=None, test_id='independent'):
    materialize(repo)
    return VariantSimulation(repo, variant[0], variant, test_id, data or fixture())


def test_each_variant_executes_same_day_independently(repo):
    a = make(repo,'A01'); b = make(repo,'A02')
    a.initialize(); b.initialize()
    old_b = b.store.load()
    assert a.run_day('2025-08-04', ScriptedSmokeAgent())['status'] == 'FILLED'
    assert b.store.load() == old_b
    assert b.run_day('2025-08-04', ScriptedSmokeAgent())['status'] == 'FILLED'
    assert a.store.root != b.store.root
    assert '/variants/A01/simulations/' in str(a.store.root)
    assert a.store.load()['initial_capital_cny'] == '200000.00'
    assert read_json(repo/'strategies/A/variants/A01/holdings.json')['status'] == 'NOT_INITIALIZED'


def test_future_tail_cannot_change_today_prompt(repo, tmp_path_factory):
    materialize(repo)
    other = tmp_path_factory.mktemp('same-prefix')
    shutil.copytree(repo, other, dirs_exist_ok=True)
    one = fixture(); two = copy.deepcopy(one)
    for day, stocks in two['bars'].items():
        if day > '2025-08-01':
            for bar in stocks.values():
                bar['open'] = '999.00'; bar['close'] = '1000.00'
    two['evidence'] = [{'published_at':'2025-08-08T10:00:00+08:00', 'source':'TEST_ONLY', 'text':'FUTURE_WINNER_SECRET'}]
    a = VariantSimulation(repo,'A','A02','same',one)
    b = VariantSimulation(other,'A','A02','same',two)
    ar = a.prepare('2025-08-04'); br = b.prepare('2025-08-04')
    assert ar['prompt'] == br['prompt']
    assert a._private_fingerprint != b._private_fingerprint
    assert a._private_fingerprint not in ar['prompt']
    assert 'FUTURE_WINNER_SECRET' not in ar['prompt']


def test_each_input_uses_own_full_file_not_legacy_snippet(repo):
    materialize(repo)
    old = repo/'strategies/A/ai_input_template.md'
    old.write_text('LEGACY_TEMPLATE_MUST_NOT_BE_USED')
    s = VariantSimulation(repo,'A','A01','own',fixture())
    r = s.prepare('2025-08-04')
    assert 'LEGACY_TEMPLATE_MUST_NOT_BE_USED' not in r['prompt']
    assert 'A01' in r['prompt'] and '{{HOLDINGS_JSON}}' not in r['prompt']
    manifest = read_json(s.store.root/'manifest.json')
    assert list(manifest['template_sha256']) == ['strategies/A/variants/A01/prompt.md']


def test_insufficient_data_is_not_retried_until_ready(repo):
    s = make(repo)
    class Agent:
        calls = 0
        def decide(self, request, errors):
            self.calls += 1
            answer = decision_base(request)
            answer.update(status='INSUFFICIENT_DATA', action=None, order_proposal=None, summary='缺少历史公告，不能可靠判断。')
            return answer
    agent = Agent()
    with pytest.raises(DecisionUnavailable):
        s.run_day('2025-08-04',agent)
    assert agent.calls == 1
    assert len(s.store.events()) == 1
    assert (s.store.root/'requests/2025-08-04/unavailable.json').exists()


def test_candidate_used_for_new_run_not_retroactively(repo):
    s = make(repo)
    s.initialize()
    old = s.store.load()
    PromptLab(repo,'A02').run(stable_patch,lambda p:{'purpose':'STABILITY','passed':True,'level':'REGRESSION_ONLY'},['NONREADY'])
    with pytest.raises(ValidationError,match='inputs changed'):
        VariantSimulation(repo,'A','A02','independent',fixture()).initialize()
    new = VariantSimulation(repo,'A','A02','new-trial',fixture())
    assert new.prompt_path.endswith('prompt_versions/v001.md')
    assert s.store.load() == old


def test_future_reference_quote_cannot_be_used(repo):
    s = make(repo)
    req=s.prepare('2025-08-04')
    answer=ScriptedSmokeAgent().decide(req,[])
    answer['order_proposal']['reference_price_cny']='999.00'
    with pytest.raises(ValidationError,match='visible history'):
        s.apply('2025-08-04',answer)
