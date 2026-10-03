"""Explicit isolated prompt experiments; no outcome feedback or formal promotion."""
import copy
from datetime import date
from decimal import Decimal
from pathlib import Path

from .simulation import Store, digest, identifier, read_json, require
from .variant_prompts import MAX_ROUNDS, PromptLab, variant_root, validate_prompt


CAPITAL_REVIEW_APPENDIX = """

## 本次收益改进对照实验：仓位与机会成本复核
这是用户授权的新隔离测试候选，完整保留上面的策略意图、股票范围和风险偏好。
只在当前资料充分时，比较买入、卖出、继续持有和保留现金的机会成本。
若原策略支持交易，请同时说明仓位对账户收益的实际贡献、下行情景和集中风险。
不要因输出示例使用100股就机械选择最小一手；数量应来自本变体偏好、证据强度和账户承受能力。
也不得为了提高测试收益默认满仓、强迫交易、放宽证据核查或用固定技术阈值替代AI判断。
对已有持仓重新检查当时理由是否仍成立，不把原始目标权重当必须保持的机械比例。
缺财务、行业或事件事实时照常返回资料不足，不把缺口转成有利判断。
本候选在任何本轮评分可见前冻结；后续收益和赢家不能回写到该时点判断。
"""


def ae_variants(repo):
    index = read_json(Path(repo) / 'strategies/index.json')
    return [v for s in index['strategies'] if s['strategy_id'] in 'ABCDE' and s['type'] != 'RESERVED'
            for v in s['variants']]


def freeze_experiment(repo, experiment_id, plan, *, appendix=CAPITAL_REVIEW_APPENDIX):
    """Reserve one durable round per variant, save both arms, keep global pointers.

    Failed/interrupted attempts consume a round exactly as stability refinement
    does. This explicit user experiment does not feed scores into PromptLab.
    """
    repo = Path(repo).resolve()
    identifier(experiment_id)
    require(plan.get('user_authorization') and plan.get('objective') == 'ISOLATED_RETURN_COMPARISON',
            'experiment requires explicit user research authorization')
    require(plan['variants'] == ae_variants(repo), 'plan must enumerate all existing A-E variants')
    targets = plan['targets']
    dates = [x['date'] for x in targets]
    require(dates == sorted(set(dates)) and len(dates) >= 2, 'experiment target order invalid')
    for day in dates:
        date.fromisoformat(day)
    if all(x.get('capital_interval_end') for x in targets):
        require(all(x['date'] < x['capital_interval_end'] for x in targets) and
                all(a['capital_interval_end'] < b['date'] for a, b in zip(targets, targets[1:])),
                'development and holdout evaluation windows overlap')
    phases = [x['phase'] for x in targets]
    require(phases[0] == 'DEVELOPMENT' and all(x == 'HOLDOUT' for x in phases[1:]),
            'development must precede frozen holdout cases')
    store = Store(repo / 'runs/experiments' / experiment_id)
    plan_hash = digest(plan)
    with store.lock():
        frozen = store.path('manifest.json')
        if frozen.exists():
            manifest = read_json(frozen)
            require(manifest['plan_sha256'] == plan_hash and manifest['appendix_sha256'] == digest(appendix),
                    'frozen experiment changed; use a new experiment_id')
            return manifest
        require(not any(any((repo / 'runs/evaluations' / (experiment_id + '-' + arm) / 'scores').glob('*/*.json'))
                        for arm in ('baseline', 'candidate')),
                'cannot freeze a candidate after seeing experiment outcomes')
        selections = {'baseline': {}, 'candidate': {}}
        for variant in plan['variants']:
            lab = PromptLab(repo, variant)
            with lab.lock():
                root = variant_root(repo, variant)
                current = read_json(root / 'simulation_prompt.json')
                path = (root / current['path']).resolve()
                require(path.is_relative_to(root), 'baseline prompt path escape')
                text = path.read_text(encoding='utf-8')
                require(digest(text) == current['sha256'], 'baseline prompt hash mismatch')
                baseline = (root / 'prompt_versions/v000.md').read_text(encoding='utf-8')
                validate_prompt(text, baseline)
                selections['baseline'][variant] = {k: current[k] for k in ('version', 'path', 'sha256')}
                round_store = Store(root)
                registration = f'experiment-prompts/{experiment_id}/registration.json'
                if round_store.path(registration).exists():
                    saved = read_json(round_store.path(registration))
                    require(saved['plan_sha256'] == plan_hash and saved['appendix_sha256'] == digest(appendix),
                            'interrupted candidate registration changed')
                    require(saved['baseline_selection'] == selections['baseline'][variant],
                            'interrupted experiment baseline changed')
                    selection = saved['selection']
                    require(digest((root / selection['path']).read_text(encoding='utf-8')) == selection['sha256'],
                            'registered candidate changed')
                else:
                    state = read_json(lab.state_path)
                    used = state.get('rounds_used')
                    require(type(used) is int and 0 <= used < MAX_ROUNDS, 'variant improvement budget exhausted or damaged')
                    recorded = [int(p.name.split('-')[1]) for p in (root / 'improvements').glob('round-*')]
                    require(not recorded or max(recorded) <= used, 'improvement counter moved backwards')
                    n = used + 1
                    # Reserve before writing or validating the proposed candidate.
                    state['rounds_used'] = n
                    round_store.write('improvement_state.json', state)
                    round_store.write(f'improvements/round-{n:02d}/request.json', {
                        'round': n, 'objective': 'USER_AUTHORIZED_ISOLATED_RETURN_EXPERIMENT',
                        'experiment_id': experiment_id, 'future_prices_provided': False,
                        'performance_feedback_provided': False, 'automatic_formal_promotion': False})
                    candidate = text + appendix
                    validate_prompt(candidate, baseline)
                    candidate_path = f'experiment-prompts/{experiment_id}/candidate.md'
                    round_store.write(candidate_path, candidate)
                    selection = {'version': experiment_id + '-r' + str(n), 'path': candidate_path,
                                 'sha256': digest(candidate)}
                    round_store.write(registration, {'round': n, 'plan_sha256': plan_hash,
                        'appendix_sha256': digest(appendix), 'selection': selection,
                        'baseline_selection': selections['baseline'][variant]})
                    round_store.write(f'improvements/round-{n:02d}/result.json', {
                        'round': n, 'accepted': True, 'scope': 'EXPLICIT_EXPERIMENT_ONLY',
                        'candidate_sha256': selection['sha256'], 'automatic_formal_promotion': False,
                        'global_simulation_pointer_changed': False})
                selections['candidate'][variant] = selection
        manifest = {'experiment_id': experiment_id, 'plan': copy.deepcopy(plan), 'plan_sha256': plan_hash,
                    'appendix_sha256': digest(appendix), 'prompt_selections': selections,
                    'future_outcomes_used_to_create_candidate': False, 'formal_promotion': False,
                    'kind': 'INDEPENDENT_POINT_CASES_NOT_CONTINUOUS_YEAR_BACKTEST'}
        store.write('manifest.json', manifest)
        return manifest


def require_all_decisions_locked(repo, manifest):
    """No arm/case gets outcomes until every planned AI decision is sealed."""
    repo = Path(repo).resolve()
    require(digest(manifest['plan']) == manifest['plan_sha256'], 'frozen experiment plan changed')
    for arm in ('baseline', 'candidate'):
        for variant in manifest['plan']['variants']:
            selection = manifest['prompt_selections'][arm][variant]
            identifier(selection['version'])
            root = variant_root(repo, variant)
            path = (root / selection['path']).resolve()
            require(path.is_relative_to(root) and path.is_file(), 'experiment prompt path invalid')
            text = path.read_text(encoding='utf-8')
            require(digest(text) == selection['sha256'], 'frozen experiment strategy prompt changed')
            validate_prompt(text, (root / 'prompt_versions/v000.md').read_text(encoding='utf-8'))
    for arm in ('baseline', 'candidate'):
        eid = manifest['experiment_id'] + '-' + arm
        for variant in manifest['plan']['variants']:
            for target in manifest['plan']['targets']:
                folder = repo / 'runs/evaluations' / eid
                entry = read_json(folder / f"entries/{variant}/{target['date']}.json")
                decision = read_json(folder / f"decisions/{variant}/{target['date']}.json")
                lock = read_json(folder / f"decisions/{variant}/{target['date']}.lock.json")
                require(lock.get('locked') is True and lock.get('future_outcomes_seen_by_decision_phase') is False,
                        'experiment decision not sealed before outcomes')
                require(digest(entry) == lock.get('entry_sha256') and digest(decision) == lock['decision_sha256'],
                        'experiment lock changed')
                require(entry['prompt_selection'] == manifest['prompt_selections'][arm][variant],
                        'experiment arm prompt selection changed')
                request = read_json(repo / entry['request_path'])
                require(digest(request) == lock['request_sha256'] and digest(request['prompt']) == lock['prompt_sha256'],
                        'experiment request changed')
                require((repo / entry['ai_input_path']).read_text(encoding='utf-8') == request['prompt'],
                        'saved experiment AI input changed')
                require(digest(read_json(repo / entry['time_travel_path'])) == lock['time_travel_sha256'],
                        'saved experiment time-travel input changed')
    return True


def compare_experiment(repo, manifest):
    require_all_decisions_locked(repo, manifest)
    repo = Path(repo).resolve()
    rows = []
    for variant in manifest['plan']['variants']:
        for target in manifest['plan']['targets']:
            arms = {}
            for arm in ('baseline', 'candidate'):
                result = read_json(repo / 'runs/evaluations' / (manifest['experiment_id'] + '-' + arm) /
                                   f"scores/{variant}/{target['date']}.json")
                score = next(x for x in result['scores'] if x['horizon_sessions'] == manifest['plan']['horizon_sessions'])
                if score['status'] == 'SCORED' and target.get('capital_interval_end'):
                    require(score['date'] == target['capital_interval_end'], 'score interval differs from frozen experiment')
                arms[arm] = {'decision_status': result.get('decision_status', 'READY'), 'action': result['action'],
                             'execution': result['execution'], 'score': score}
            valid = all(x['score']['status'] == 'SCORED' for x in arms.values())
            rows.append({'variant': variant, 'phase': target['phase'], 'target_date': target['date'],
                         'arms': arms, 'comparable': valid,
                         'return_change_percentage_points': str(Decimal(arms['candidate']['score']['actual_return_pct']) -
                             Decimal(arms['baseline']['score']['actual_return_pct'])) if valid else None})
    summary = []
    for variant in manifest['plan']['variants']:
        cases = [r for r in rows if r['variant'] == variant and r['phase'] == 'HOLDOUT']
        complete = all(r['comparable'] for r in cases)
        change = sum((Decimal(r['return_change_percentage_points']) for r in cases), Decimal(0)) / len(cases) if complete else None
        dd_worse = any(Decimal(r['arms']['candidate']['score']['max_daily_drawdown_pct']) >
                       Decimal(r['arms']['baseline']['score']['max_daily_drawdown_pct']) for r in cases if r['comparable'])
        summary.append({'variant': variant, 'holdout_cases': len(cases), 'all_comparable': complete,
                        'mean_holdout_return_change_percentage_points': str(change) if change is not None else None,
                        'any_holdout_drawdown_worse': dd_worse,
                        'result': 'OBSERVED_IMPROVEMENT_WITHOUT_WORSE_DRAWDOWN' if complete and change > 0 and not dd_worse
                                  else 'NO_ACCEPTED_IMPROVEMENT' if complete else 'INSUFFICIENT_EVIDENCE',
                        'formal_promotion': False})
    result = {'experiment_id': manifest['experiment_id'], 'rows': rows, 'variant_summary': summary,
              'aggregation': 'Mean independent holdout case return differences; not a compounded yearly track record.',
              'annualization': 'Mathematical conversion only, not a prediction.', 'formal_promotion': False}
    Store(repo / 'runs/experiments' / manifest['experiment_id']).write('comparison.json', result)
    return result
