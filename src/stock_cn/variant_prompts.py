"""Standalone variant prompts and durable maximum-ten-round stability refinement.

No price-outcome optimization; no model/API invoked by default.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

MAX_ROUNDS = 10
START = '<!-- IMMUTABLE_STRATEGY_START -->'
END = '<!-- IMMUTABLE_STRATEGY_END -->'
ISSUES = {
    'STRICT_JSON': '只返回一个JSON对象，中文结论放summary字段；不要在JSON外输出解释或Markdown。',
    'IDENTITY': '原样回填variant_id、mode、日期、账户revision及输入版本；不使用其他变体的状态。',
    'NONREADY': '资料不足、未授权或未初始化是正常未执行状态，不是HOLD；action和order_proposal均为null，不为通过校验强行交易。',
    'CAUSALITY': '视自己处于本次信息截止时刻。不能使用随后价格、未来财报、后来新闻、后验赢家或测试期最终收益改写当天判断。',
    'PROVENANCE': '证据同时记录来源和当时可知的发布时间；无法核查就报告缺口，不编造检索或引用。',
}


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = value if isinstance(value, str) else dump(value)
    fd, temp = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def variant_root(repo, variant):
    if not isinstance(variant, str) or not re.fullmatch('[A-Z][0-9]{2}', variant):
        raise ValueError('invalid variant identifier')
    repo = Path(repo).resolve()
    root = repo / 'strategies' / variant[0] / 'variants' / variant
    if not root.resolve().is_relative_to(repo / 'strategies'):
        raise ValueError('variant path escapes repository')
    return root


def protected(text):
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('missing or duplicated protected strategy block')
    return text.split(START, 1)[1].split(END, 1)[0]


def validate_prompt(text, baseline):
    if not isinstance(text, str) or len(text) > 100000:
        raise ValueError('invalid full prompt size')
    if protected(text) != protected(baseline):
        raise ValueError('investment intent, risk preference or hard boundary changed')
    needed = {'RUN_CONTEXT', 'HOLDINGS_JSON', 'HOLDINGS_TABLE_ROWS', 'PREVIOUS_DECISION_SUMMARY', 'EVIDENCE_AND_TOOL_CONTEXT'}
    actual = set(re.findall(r'\{\{([A-Z_]+)\}\}', text))
    if not needed <= actual or actual - (needed | {'AUTHORIZED_UNIVERSE'}):
        raise ValueError('dynamic input contract changed')
    for word in ('BUY', 'SELL', 'HOLD', 'INSUFFICIENT_DATA'):
        if word not in text:
            raise ValueError('output contract missing ' + word)
    return True


def full_prompt(series, variant, intent, preference, template):
    fixed = {'series_id': series['strategy_id'], 'variant_id': variant,
             'initial_capital_cny': 200000, 'account_scope': 'ONE_INDEPENDENT_VARIANT',
             'allowed_symbols': series.get('symbols'), 'excluded_boards': ['科创板'],
             'max_decisions_per_market_day': 1, 'max_orders_per_market_day': 1,
             'paper_only': True, 'no_future_information': True}
    text = f'# {variant}：独立执行的完整AI提示词\n\n'
    text += '本文件已展开全部内容，只注入本次日期、账户和证据，不再在运行时拼接其他变体。\n'
    text += START + '\n' + dump(fixed) + '\n## 不可自动改变的投资意图\n' + intent
    text += '\n## 本变体唯一的风险与研究偏好\n' + preference + '\n' + END + '\n\n'
    template = re.sub(r'(?m)^(?:本次按run_context指定的变体执行：|本次只用指定变体：|变体只取本次指定的一个：|仅按指定变体：).*$', '本次只执行上面固定的变体偏好，不再从系列其他变体中选择。', template)
    text += '## 已展开的资料查询、账户分析与输出要求\n' + template
    text += f'\n\n## {variant}的优先执行说明\n只执行上面本变体的偏好；原系列模板对其他变体的概述只是背景，不能切换变体或混用账户。\n'
    text += '系列根目录原holdings.json仅为迁移前入口；本次唯一账户路径以RUN_CONTEXT.account_path为准。\n'
    text += '模拟将自己置于信息截止时刻；后续市场变化未知，账户余额和股数只能来自当前快照。\n'
    text += 'READY的action只允许BUY、SELL、HOLD；每次至多一个order_proposal。\n'
    text += '只返回一个JSON对象，中文解释放summary；缺资料返回INSUFFICIENT_DATA且action/order_proposal为null。\n'
    text += '自我改进只改表达清晰度和稳定性，每变体累计最多10轮；不按后续收益挑选当天提示词。\n'
    validate_prompt(text, text)
    return text


def materialize(repo):
    """Idempotent migration; never reset an existing variant or overwrite its prompt."""
    repo = Path(repo).resolve()
    index_path = repo / 'strategies/index.json'
    index = read(index_path)
    previous = {x['variant_id']: x for x in index.get('variants', [])}
    if index.get('execution_unit') != 'VARIANT' and (index.get('formal_execution_enabled') or any(x.get('enabled') for x in index['strategies'])):
        raise ValueError('active series account requires explicit migration; not resetting funds')
    registry = []
    for series in index['strategies']:
        if series['type'] == 'RESERVED':
            continue
        folder = repo / 'strategies' / series['strategy_id']
        intent = (folder / 'prompt.md').read_text(encoding='utf-8')
        template = (folder / 'ai_input_template.md').read_text(encoding='utf-8')
        init = read(folder / 'init.json')
        for variant in series['variants']:
            root = variant_root(repo, variant)
            if not (root / 'prompt.md').exists():
                preference = (folder / 'variants' / (variant + '.md')).read_text(encoding='utf-8')
                text = full_prompt(series, variant, intent, preference, template)
                write(root / 'prompt.md', text)
                write(root / 'prompt_versions/v000.md', text)
            if not (root / 'init.json').exists():
                obj = copy.deepcopy(init)
                obj.update(variant_id=variant, account_scope='INDEPENDENT_VARIANT', initial_capital_cny=200000)
                write(root / 'init.json', obj)
            if not (root / 'holdings.json').exists():
                positions = [{'symbol': s['symbol'], 'name': s.get('name'), 'quantity': None,
                              'sellable_quantity': None, 'average_cost_cny': None, 'valuation_price_cny': None}
                             for s in init.get('stocks', [])]
                write(root / 'holdings.json', {'strategy_id': series['strategy_id'], 'variant_id': variant,
                    'status': 'NOT_INITIALIZED', 'date': None, 'initial_capital_cny': 200000,
                    'total_equity_cny': None, 'cash_cny': None, 'positions': positions,
                    '_meta': {'mode': 'FORMAL', 'paper_only': True, 'revision': 0, 'execution_enabled': False},
                    'note': '该变体独立的正式模拟账户尚未初始化；测试余额在simulations中，不从系列共享余额读取。'})
                write(root / 'holdings.md', f'# {variant} 独立持仓\n\n尚未初始化。计划初始总资产20万元；现金、日期和股数待该账户实际初始化。\n')
            if not (root / 'simulation_prompt.json').exists():
                write(root / 'simulation_prompt.json', {'version': 'v000', 'path': 'prompt.md', 'sha256': sha((root / 'prompt.md').read_text(encoding='utf-8')), 'scope': 'NEW_SIMULATION_ONLY'})
            if not (root / 'formal_prompt.json').exists():
                write(root / 'formal_prompt.json', {'version': 'v000', 'path': 'prompt.md',
                    'sha256': sha((root / 'prompt.md').read_text(encoding='utf-8')),
                    'scope': 'FORMAL_BASELINE_NOT_EXECUTION_AUTHORIZATION'})
            if not (root / 'improvement_state.json').exists():
                write(root / 'improvement_state.json', {'max_rounds': MAX_ROUNDS, 'rounds_used': 0,
                    'status': 'READY', 'active_prompt_version': 'v000', 'reset_requires_user_authorization': True})
            registry.append({'variant_id': variant, 'series_id': series['strategy_id'],
                'status': 'DRAFT', 'enabled': False, 'initial_capital_cny': 200000,
                'prompt': str((root / 'prompt.md').relative_to(repo)),
                'initialization': str((root / 'init.json').relative_to(repo)),
                'holdings': str((root / 'holdings.json').relative_to(repo)),
                'simulation_directory': str((root / 'simulations').relative_to(repo))})
            for key in ('status', 'enabled', 'initial_capital_cny'):
                if key in previous.get(variant, {}):
                    registry[-1][key] = previous[variant][key]
        series['execution_role'] = 'GROUP_ONLY'
        series.pop('active_variant', None)
    index.update(schema_version='0.5-draft', execution_unit='VARIANT',
                 capital_scope='200000_CNY_PER_INDEPENDENT_VARIANT', variants=registry,
                 prompt_improvement={'max_rounds_per_variant': MAX_ROUNDS, 'objective': 'STABILITY_NOT_FUTURE_RETURNS'})
    write(index_path, index)
    return registry


def approve_simulation_prompt_for_formal(repo, variant, *, expected_version, authorized=False):
    """Promote the exact tested prompt pointer, never holdings/P&L or execution state.

    This does NOT enable the variant or global formal execution.
    """
    if authorized is not True:
        raise ValueError('explicit user authorization required for formal prompt promotion')
    root = variant_root(repo, variant)
    simulation = read(root / 'simulation_prompt.json')
    if simulation.get('version') != expected_version:
        raise ValueError('tested prompt version changed; re-check before promotion')
    chosen = (root / simulation['path']).resolve()
    if not chosen.is_relative_to(root.resolve()):
        raise ValueError('simulation prompt path escape')
    text = chosen.read_text(encoding='utf-8')
    if sha(text) != simulation.get('sha256'):
        raise ValueError('simulation prompt hash mismatch')
    baseline = (root / 'prompt_versions/v000.md').read_text(encoding='utf-8')
    validate_prompt(text, baseline)
    pointer = {'version': simulation['version'], 'path': simulation['path'],
               'sha256': simulation['sha256'],
               'scope': 'FORMAL_PROMPT_APPROVED_NOT_EXECUTION_AUTHORIZATION'}
    write(root / 'formal_prompt.json', pointer)
    return pointer


class PromptLab:
    """Reserve budget before proposing. Rejected/interrupted attempts also count.

    Only stability issue codes reach the proposer, never future return or P&L.
    Accepted candidates are experimental; they cannot promote formal execution.
    """
    def __init__(self, repo, variant):
        self.root = variant_root(repo, variant)
        self.state_path = self.root / 'improvement_state.json'
        if not self.state_path.exists():
            raise ValueError('materialize variants first')

    @contextmanager
    def lock(self):
        p = self.root / '.improvement.lock'
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValueError('another improvement is in progress; do not remove its lock') from exc
        try:
            os.close(fd)
            yield
        finally:
            p.unlink(missing_ok=True)

    def run(self, proposer, evaluator, issue_codes, *, max_rounds=10):
        if type(max_rounds) is not int or not 0 <= max_rounds <= MAX_ROUNDS:
            raise ValueError('improvement limit must be between 0 and 10')
        if not set(issue_codes) <= ISSUES.keys():
            raise ValueError('feedback must be known stability codes, not future price/performance')
        reports = []
        with self.lock():
            state = read(self.state_path)
            if type(state.get('rounds_used')) is not int or not 0 <= state['rounds_used'] <= MAX_ROUNDS:
                raise ValueError('damaged improvement budget; no implicit reset')
            recorded = [int(p.name.split('-')[1]) for p in (self.root / 'improvements').glob('round-*')]
            if recorded and max(recorded) > state['rounds_used']:
                raise ValueError('counter moved backwards; refusing reset')
            baseline = (self.root / 'prompt.md').read_text(encoding='utf-8')
            current = (self.root / 'improvements/best_prompt.md').read_text(encoding='utf-8') if (self.root / 'improvements/best_prompt.md').exists() else baseline
            validate_prompt(current, baseline)
            for _ in range(min(max_rounds, MAX_ROUNDS - state['rounds_used'])):
                state['rounds_used'] += 1
                n = state['rounds_used']
                target = self.root / 'improvements' / f'round-{n:02d}'
                target.mkdir(parents=True, exist_ok=False)
                state['status'] = 'RUNNING'
                write(self.state_path, state)
                write(target / 'before.md', current)
                write(target / 'request.json', {'round': n, 'max_rounds': MAX_ROUNDS,
                    'issue_codes': list(issue_codes), 'objective': 'STABILITY',
                    'future_prices_provided': False, 'performance_feedback_provided': False})
                report = {'round': n, 'accepted': False, 'automatic_formal_promotion': False}
                try:
                    candidate = proposer(current, [ISSUES[c] for c in issue_codes])
                    write(target / 'candidate.md', candidate)
                    validate_prompt(candidate, baseline)
                    evaluation = evaluator(candidate)
                    write(target / 'validation.json', evaluation)
                    if evaluation.get('purpose') != 'STABILITY' or evaluation.get('passed') is not True:
                        raise ValueError('candidate failed stability validation')
                    current = candidate
                    write(self.root / 'improvements/best_prompt.md', current)
                    write(self.root / f'prompt_versions/v{n:03d}.md', current)
                    write(self.root / 'simulation_prompt.json', {'version': f'v{n:03d}', 'path': f'prompt_versions/v{n:03d}.md', 'sha256': sha(current), 'scope': 'NEW_SIMULATION_ONLY'})
                    report.update(accepted=True, candidate_sha256=sha(current), validation_level=evaluation.get('level'))
                    state.update(status='CANDIDATE_READY', best_candidate_version=f'v{n:03d}')
                except Exception as exc:
                    report['error'] = f'{type(exc).__name__}: {exc}'
                    state['status'] = 'REJECTED'
                write(target / 'result.json', report)
                write(self.state_path, state)
                reports.append(report)
                if report['accepted']:
                    break
            if state['rounds_used'] >= MAX_ROUNDS:
                state['status'] = 'LIMIT_REACHED'
                write(self.state_path, state)
        return {'rounds_used': state['rounds_used'], 'max_rounds': MAX_ROUNDS,
                'status': state['status'], 'rounds': reports, 'active_prompt_unchanged': True}


def stable_patch(current, issues):
    return current + '\n\n## 本轮输出稳定性补充（不改变投资策略）\n' + '\n'.join('- ' + s for s in issues) + '\n'
