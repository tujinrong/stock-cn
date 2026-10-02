"""Variant-isolated execution and prefix-invariant historical AI inputs."""
from __future__ import annotations

import copy
from datetime import datetime

from .simulation import Simulation as BaseSimulation, Store, digest, number, read_json, require
from .variant_prompts import variant_root, validate_prompt
from .time_travel import append_time_travel_prompt, build_time_travel_context


class DecisionUnavailable(RuntimeError):
    """Legitimate insufficient information, NOT a format error to coerce into READY."""


class VariantSimulation(BaseSimulation):
    def __init__(self, repo, series, variant, test_id, data):
        super().__init__(repo, series, variant, test_id, data)
        self.variant_mode = read_json(self.repo / 'strategies/index.json').get('execution_unit') == 'VARIANT'
        if not self.variant_mode:
            return
        root = variant_root(self.repo, variant)
        selected = root / 'prompt.md'
        if (root / 'simulation_prompt.json').exists():
            pointer = read_json(root / 'simulation_prompt.json')
            selected = (root / pointer['path']).resolve()
            require(selected.is_relative_to(root.resolve()), 'candidate prompt path escape')
            require(digest(selected.read_text(encoding='utf-8')) == pointer['sha256'], 'candidate prompt hash mismatch')
        full = selected.read_text(encoding='utf-8')
        validate_prompt(full, (root / 'prompt_versions/v000.md').read_text(encoding='utf-8'))
        self.prompt_path = str(selected.relative_to(self.repo))
        self.templates = {self.prompt_path: full}
        self.init = read_json(root / 'init.json')
        require(self.init.get('variant_id') == variant, 'initialization belongs to another variant')
        test_root = root / 'simulations' / test_id
        require(test_root.resolve().is_relative_to(root.resolve()), 'simulation path escape')
        self.store = Store(test_root)
        self.fingerprint = digest({'variant': variant, 'init': self.init, 'prompt': full,
                                   'dataset': self.data, 'fees': {k: str(v) for k, v in self.fees.items()}})
        self._private_fingerprint = self.fingerprint

    def initialize(self):
        if not getattr(self, 'variant_mode', False):
            return super().initialize()
        public_fingerprint = self.fingerprint
        self.fingerprint = self._private_fingerprint
        try:
            return super().initialize()
        finally:
            self.fingerprint = public_fingerprint

    def prepare(self, day):
        if not self.variant_mode:
            return super().prepare(day)
        self.initialize()
        days = self.data['sessions']
        require(day in days and days.index(day) > 0, 'not a replay session')
        cutoff = days[days.index(day)-1] + 'T15:00:00+08:00'
        when = datetime.fromisoformat(cutoff)
        known = {s: m for s, m in self.data['instruments'].items()
                 if not m.get('known_at') or datetime.fromisoformat(m['known_at']) <= when}
        include_evidence = bool(self.data.get('time_travel_include_evidence', False))
        evidence = ([e for e in self.data.get('evidence', [])
                     if datetime.fromisoformat(e['published_at']) <= when]
                    if include_evidence else [])
        travel = build_time_travel_context(
            self.data, day, cutoff[:10], symbols=sorted(known), ignore_news=not include_evidence)
        runtime_prompt = append_time_travel_prompt(self.templates[self.prompt_path], travel)
        visible = {'cutoff': cutoff, 'holdings': self.store.load(), 'prompt': runtime_prompt,
                   'bars': {d: {s: b for s, b in rows.items() if s in known}
                            for d, rows in self.data['bars'].items() if d <= cutoff[:10]},
                   'evidence': evidence, 'known_symbols': sorted(known),
                   'time_travel': travel}
        view = copy.copy(self)
        view.data = copy.deepcopy(self.data)
        view.data['instruments'] = known
        view.data['evidence'] = evidence
        view.fingerprint = digest(visible)
        # Aliases exist only in this rendering view. Stored hashes/snapshots name
        # the actual standalone variant file, not the old shared template.
        view.templates = {
            f'strategies/{self.series}/ai_input_template.md': runtime_prompt,
            f'strategies/{self.series}/variants/{self.variant}.md': ''}
        request = BaseSimulation.prepare(view, day)
        if not request.get('completed'):
            request['context']['time_travel'] = True
            request['context']['time_travel_target_date'] = day
            request['context']['time_travel_knowledge_cutoff'] = travel['knowledge_cutoff']
            request['time_travel'] = travel
            request['prompt_sha256'] = digest(request['prompt'])
            view.store.write(f"requests/{day}/request.json", request)
            view.store.write(f"requests/{day}/time_travel.json", travel)
        return request

    def validate_decision(self, response, request):
        if isinstance(response, dict) and response.get('status') in {
            'INSUFFICIENT_DATA', 'NOT_INITIALIZED', 'NOT_AUTHORIZED', 'INVALID_INPUT'}:
            c = request['context']
            for field in ('strategy_id', 'variant_id', 'mode', 'run_id', 'decision_id', 'date', 'input_revision', 'input_commit'):
                require(response.get(field) == c[field], 'unavailable response identity mismatch')
            require(response.get('action') is None and response.get('order_proposal') is None,
                    'non-READY response cannot contain a trade')
            require(isinstance(response.get('summary'), str) and response['summary'], 'missing reason')
            self.store.write(f"requests/{c['date']}/unavailable.json", response)
            raise DecisionUnavailable(response['status'] + ': ' + response['summary'])
        super().validate_decision(response, request)
        if self.variant_mode and response['order_proposal']:
            order = response['order_proposal']
            rows = request['market'].get(order['symbol'], [])
            require(bool(rows), 'no point-in-time quote for selected stock')
            last = rows[-1]
            require(number(order['reference_price_cny']) == number(last['close']), 'reference quote does not match visible history')
            require(order['quote_source'] == last['source'], 'reference quote source is not in input')
            require(order['quote_time'] == request['context']['information_cutoff'], 'reference quote must use the replay cutoff')
