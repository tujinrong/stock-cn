import pytest
from stock_cn.variant_prompts import materialize, PromptLab, stable_patch, validate_prompt, read, write


@pytest.fixture
def prompt_repo(tmp_path):
    write(tmp_path / 'strategies/index.json', {'formal_execution_enabled': False, 'strategies': [
        {'strategy_id':'A','type':'FIXED','enabled':False,'symbols':['600036.SH'],'variants':['A01','A02','A03']},
        {'strategy_id':'B','type':'RESERVED','enabled':False,'variants':[]}]})
    folder = tmp_path / 'strategies/A'
    write(folder / 'prompt.md', 'Use evidence; control risk; no fixed trading formula.')
    for v in ['A01','A02','A03']:
        write(folder / f'variants/{v}.md', v + ': independent risk preference')
    write(folder / 'ai_input_template.md', '\n'.join('{{'+k+'}}' for k in ['RUN_CONTEXT','HOLDINGS_JSON','HOLDINGS_TABLE_ROWS','PREVIOUS_DECISION_SUMMARY','EVIDENCE_AND_TOOL_CONTEXT']))
    write(folder / 'init.json', {'initial_capital_cny':200000,'stocks':[],'opening_method':'CASH_ONLY'})
    materialize(tmp_path)
    return tmp_path


def test_complete_independent_files(prompt_repo):
    root = prompt_repo / 'strategies/A/variants'
    for v in ['A01','A02','A03']:
        text = (root / v / 'prompt.md').read_text()
        assert v + ': independent risk preference' in text
        assert 'HOLDINGS_JSON' in text and 'INSUFFICIENT_DATA' in text
        assert read(root/v/'holdings.json')['variant_id'] == v
        assert read(root/v/'init.json')['initial_capital_cny'] == 200000
    assert not (prompt_repo/'strategies/B/variants').exists()


def test_materialization_does_not_reset(prompt_repo):
    p = prompt_repo/'strategies/A/variants/A01/prompt.md'
    p.write_text(p.read_text()+'\nmanual amendment\n')
    before = p.read_text()
    index = read(prompt_repo/'strategies/index.json')
    index['variants'][0]['enabled'] = True
    write(prompt_repo/'strategies/index.json', index)
    materialize(prompt_repo)
    assert p.read_text() == before
    assert read(prompt_repo/'strategies/index.json')['variants'][0]['enabled'] is True


def test_ten_attempts_including_rejected_candidates(prompt_repo):
    calls = []
    def bad(current, issues):
        calls.append(1)
        return 'not a full prompt'
    result = PromptLab(prompt_repo, 'A01').run(bad, lambda p: {}, ['STRICT_JSON'])
    assert result['rounds_used'] == 10 and result['status'] == 'LIMIT_REACHED'
    result2 = PromptLab(prompt_repo, 'A01').run(bad, lambda p: {}, ['STRICT_JSON'])
    assert result2['rounds_used'] == 10 and len(calls) == 10


@pytest.mark.parametrize('maximum', [-1,11,100,True,1.5])
def test_illegal_limit_rejected(prompt_repo, maximum):
    with pytest.raises(ValueError):
        PromptLab(prompt_repo,'A01').run(stable_patch, lambda p: {}, [], max_rounds=maximum)
    assert read(prompt_repo/'strategies/A/variants/A01/improvement_state.json')['rounds_used'] == 0


def test_success_early_stop_and_separate_candidate(prompt_repo):
    root = prompt_repo/'strategies/A/variants/A02'
    original = (root/'prompt.md').read_text()
    result = PromptLab(prompt_repo,'A02').run(stable_patch, lambda p: {'purpose':'STABILITY','passed':True,'level':'STATIC_ONLY'}, ['NONREADY','CAUSALITY'])
    assert result['rounds_used'] == 1 and result['rounds'][0]['accepted']
    assert (root/'prompt.md').read_text() == original
    assert read(root/'simulation_prompt.json')['path'] == 'prompt_versions/v001.md'
    assert '未来财报' in (root/'improvements/best_prompt.md').read_text()
    assert read(prompt_repo/'strategies/A/variants/A01/improvement_state.json')['rounds_used'] == 0


def test_investment_intent_cannot_be_changed(prompt_repo):
    root=prompt_repo/'strategies/A/variants/A01'
    base=(root/'prompt.md').read_text()
    with pytest.raises(ValueError, match='intent'):
        validate_prompt(base.replace('initial_capital_cny": 200000','initial_capital_cny": 300000'),base)


def test_future_profit_feedback_is_not_allowed(prompt_repo):
    with pytest.raises(ValueError, match='feedback'):
        PromptLab(prompt_repo,'A01').run(stable_patch, lambda p: {}, ['FINAL_RETURN_20_PERCENT'])


def test_return_optimizing_evaluator_rejected(prompt_repo):
    result=PromptLab(prompt_repo,'A01').run(stable_patch,lambda p:{'purpose':'MAX_RETURN','passed':True},['STRICT_JSON'],max_rounds=1)
    assert not result['rounds'][0]['accepted']


def test_counter_rollback_detected(prompt_repo):
    root=prompt_repo/'strategies/A/variants/A01'
    PromptLab(prompt_repo,'A01').run(lambda p,i:'bad',lambda p:{},[],max_rounds=1)
    state=read(root/'improvement_state.json'); state['rounds_used']=0;write(root/'improvement_state.json',state)
    with pytest.raises(ValueError,match='backwards'):
        PromptLab(prompt_repo,'A01').run(stable_patch,lambda p:{},[])
