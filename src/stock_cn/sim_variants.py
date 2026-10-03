"""Variant-isolated execution and prefix-invariant historical AI inputs."""
from __future__ import annotations

import copy
import re
from datetime import datetime
from pathlib import Path

from .simulation import Simulation as BaseSimulation, Store, digest, money, number, read_json, require
from .research_state import sync_simulation_state
from .research_inputs import load_research_inputs, research_input_root
from .research_bundle import buy_research_preflight
from .variant_prompts import variant_root, validate_prompt
from .time_travel import append_time_travel_prompt, build_time_travel_context


class DecisionUnavailable(RuntimeError):
    """Legitimate insufficient information, NOT a format error to coerce into READY."""


class VariantSimulation(BaseSimulation):
    def __init__(self, repo, series, variant, test_id, data, *, prompt_selection=None):
        super().__init__(repo, series, variant, test_id, data)
        self.variant_mode = read_json(self.repo / 'strategies/index.json').get('execution_unit') == 'VARIANT'
        if not self.variant_mode:
            require(prompt_selection is None, 'explicit prompt selection requires independent variant mode')
            return
        root = variant_root(self.repo, variant)
        selected = root / 'prompt.md'
        pointer = prompt_selection
        if pointer is None and (root / 'simulation_prompt.json').exists():
            pointer = read_json(root / 'simulation_prompt.json')
        if pointer is not None:
            require(isinstance(pointer, dict), 'prompt selection must be an object')
            require(isinstance(pointer.get('version'), str) and
                    re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}', pointer['version']),
                    'invalid prompt selection version')
            require(isinstance(pointer.get('path'), str) and pointer['path'] and
                    not Path(pointer['path']).is_absolute(),
                    'prompt selection path must be relative to the variant')
            require(isinstance(pointer.get('sha256'), str) and
                    re.fullmatch(r'[0-9a-f]{64}', pointer['sha256']),
                    'invalid prompt selection hash')
            selected = (root / pointer['path']).resolve()
            require(selected.is_relative_to(root.resolve()), 'candidate prompt path escape')
            require(selected.is_file(), 'selected prompt file missing')
            require(digest(selected.read_text(encoding='utf-8')) == pointer['sha256'], 'candidate prompt hash mismatch')
        full = selected.read_text(encoding='utf-8')
        validate_prompt(full, (root / 'prompt_versions/v000.md').read_text(encoding='utf-8'))
        self.prompt_selection = {
            'version': pointer['version'] if pointer is not None else 'v000',
            'path': selected.relative_to(root).as_posix(), 'sha256': digest(full),
        }
        self.prompt_path = selected.relative_to(self.repo).as_posix()
        self.templates = {self.prompt_path: full}
        self.init = read_json(root / 'init.json')
        require(self.init.get('variant_id') == variant, 'initialization belongs to another variant')
        test_root = root / 'simulations' / test_id
        require(test_root.resolve().is_relative_to(root.resolve()), 'simulation path escape')
        self.store = Store(test_root)
        fingerprint_data = copy.deepcopy(self.data)
        fingerprint_data.pop('retrieved_at', None)
        self.fingerprint = digest({'variant': variant, 'init': self.init, 'prompt': full,
                                   'dataset': fingerprint_data, 'fees': {k: str(v) for k, v in self.fees.items()}})
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

    def jump_initialize(self, target_date):
        """Initialize an isolated time-travel account at target-date close.

        This is for a one-point historical jump, not for continuous backtests.
        It never rewrites a pre-existing simulation account and never touches FORMAL.
        """
        require(self.variant_mode, 'time-travel jump requires independent variant mode')
        days = self.data['sessions']
        require(target_date in days, 'time-travel target must be a supplied market session')
        require(days.index(target_date) + 1 < len(days), 'time-travel target needs a following execution session')
        with self.store.lock():
            if self.store.events():
                first = self.store.events()[0]['documents']['manifest.json']
                require(first.get('time_travel_target_date') == target_date,
                        'existing test account belongs to another time-travel target')
                require(first['input_fingerprint'] == self._private_fingerprint,
                        'inputs changed: use a new test_id')
                return self.store.load()
            cash = number(self.init['initial_capital_cny'])
            positions = []
            if self.init['opening_method'] == 'ASSUMED_EXISTING_PORTFOLIO':
                require(number(self.init['cash_weight']) + sum(number(s['weight']) for s in self.init['stocks']) == 1,
                        'initial weights do not sum to one')
                for stock in self.init['stocks']:
                    symbol = stock['symbol']
                    self.check_symbol(symbol)
                    price = number(self.bar(target_date, symbol)['close'])
                    quantity = int(number(self.init['initial_capital_cny']) * number(stock['weight']) / price / 100) * 100
                    cash -= quantity * price
                    if quantity:
                        positions.append({
                            'symbol': symbol,
                            'name': self.data['instruments'][symbol]['name'],
                            'quantity': quantity,
                            'sellable_quantity': quantity,
                            'average_cost_cny': money(price),
                            'cost_basis_cny': money(quantity * price),
                            'valuation_price_cny': money(price),
                        })
            else:
                require(not self.init.get('stocks') or all(number(s.get('weight', 0)) == 0 for s in self.init['stocks']),
                        'cash opening contains positive stock weights')
            state = {
                'strategy_id': self.series, 'status': 'SIMULATION', 'date': target_date,
                'initial_capital_cny': money(self.init['initial_capital_cny']),
                'cash_cny': money(cash), 'total_equity_cny': money(self.init['initial_capital_cny']),
                'positions': positions,
                '_meta': {
                    'schema_version': '0.4', 'mode': 'SIMULATION', 'paper_only': True,
                    'variant_id': self.variant, 'test_id': self.test_id, 'revision': 0,
                    'valuation_time': f'{target_date}T15:00:00+08:00',
                    'fees_cny': '0.00', 'last_decision_date': None,
                    'data_kind': self.data['kind'], 'time_travel_jump': True,
                },
            }
            sources = sorted({b['source'] for b in self.data['bars'][target_date].values()})
            manifest = {
                'mode': 'SIMULATION', 'submode': 'TIME_TRAVEL_JUMP',
                'series': self.series, 'variant': self.variant, 'test_id': self.test_id,
                'time_travel_target_date': target_date,
                'planned_execution_date': days[days.index(target_date) + 1],
                'input_fingerprint': self._private_fingerprint,
                'source_commit': self.source_commit,
                'fees': {k: str(v) for k, v in self.fees.items()},
                'data_kind': self.data['kind'], 'fidelity': self.data['fidelity'],
                'execution_basis': 'TARGET_CLOSE_KNOWLEDGE_NEXT_SESSION_OPEN',
                'initialization': 'TIME_TRAVEL_OPENING_BALANCE_AT_TARGET_CLOSE',
                'limitations': self.data.get('limitations', []) + [
                    'Jump account starts at target-date close; it does not recreate trades before that date.',
                    'This is a point-in-time scenario, distinct from a continuous backtest.',
                ],
                'source_version': ' / '.join(sources),
                'template_sha256': {k: digest(v) for k, v in self.templates.items()},
            }
            return self.store.commit(
                'OPENING_BALANCE', None, state,
                {'manifest.json': manifest, 'init.snapshot.json': self.init,
                 'templates.snapshot.json': self.templates})

    def prepare(self, day):
        if not self.variant_mode:
            return super().prepare(day)
        self.initialize()
        days = self.data['sessions']
        require(day in days and days.index(day) > 0, 'not a replay session')
        cutoff = days[days.index(day)-1] + 'T15:00:00+08:00'
        when = datetime.fromisoformat(cutoff)
        current_state = self.store.load()
        held_symbols = {p['symbol'] for p in current_state['positions']}
        known = {s: m for s, m in self.data['instruments'].items()
                 if not m.get('known_at') or datetime.fromisoformat(m['known_at']) <= when}
        travel_day = cutoff[:10]
        file_research = None
        namespace = self.data.get('research_namespace')
        research_manifest_path = research_input_root(
            self.repo, self.variant, travel_day, namespace=namespace) / 'manifest.json'
        if research_manifest_path.exists():
            file_research = load_research_inputs(
                self.repo, self.variant, travel_day, as_of=cutoff, namespace=namespace
            )
            require(file_research.get('mode') == 'SIMULATION',
                    'historical simulation cannot use FORMAL research inputs')
            scope = file_research.get('universe_scope') or {}
            authorized = set(scope.get('authorized_symbols') or [])
            required = authorized | held_symbols
            require(required <= set(known),
                    'research input references symbol missing from historical dataset')
            if required:
                known = {s: m for s, m in known.items() if s in required}
        include_evidence = bool(self.data.get('time_travel_include_evidence', False))
        evidence = ([e for e in self.data.get('evidence', [])
                     if datetime.fromisoformat(e['published_at']) <= when]
                    if include_evidence else [])
        travel = build_time_travel_context(
            self.data, travel_day, travel_day, symbols=sorted(known),
            ignore_news=not include_evidence, execution_date=day)
        research_state = None
        if self.spec.get('type') == 'AI_SELECT':
            file_pack = file_research.get('candidate_research_pack') if file_research else None
            file_scope = file_research.get('universe_scope') if file_research else None
            pack = file_pack if file_pack is not None else self.data.get('candidate_research_pack')
            if file_pack is not None and self.data.get('candidate_research_pack') is not None:
                require(file_pack == self.data.get('candidate_research_pack'),
                        'file candidate pack conflicts with supplied historical dataset')
            if isinstance(pack, dict) and pack.get('cutoff_date'):
                require(pack['cutoff_date'] <= travel_day,
                        'candidate research pack comes from the future')
            watchlist = self.data.get('research_watchlist')
            universe_scope = file_scope or self.data.get('universe_scope') or {
                'authorized_symbols': sorted(known),
                'coverage': 'BOUNDED_RESEARCH_CANDIDATES_ONLY',
                'not_full_a_share_claim': True,
            }
            research_state = sync_simulation_state(
                self.store.root, self.series, self.variant, travel_day,
                candidate_pack=pack,
                watchlist=watchlist,
                universe_scope=universe_scope,
                broad_source=self.data.get('broad_universe_source'),
            )
        runtime_prompt = append_time_travel_prompt(self.templates[self.prompt_path], travel,
                                                 compact=bool(self.data.get('prompt_payload_codec')))
        visible = {'cutoff': cutoff, 'holdings': self.store.load(), 'prompt': runtime_prompt,
                   'bars': {d: {s: b for s, b in rows.items() if s in known}
                            for d, rows in self.data['bars'].items() if d <= cutoff[:10]},
                   'evidence': evidence, 'known_symbols': sorted(known),
                   'time_travel': travel, 'research_state': research_state}
        view = copy.copy(self)
        view.data = copy.deepcopy(self.data)
        view.data['instruments'] = known
        view.data['evidence'] = evidence
        view.data['research_state'] = research_state
        if file_research is not None:
            view.data['official_disclosure_pack'] = file_research.get('official_disclosure_pack')
            view.data['financial_reviews'] = file_research.get('financial_reviews')
            view.data['news_research'] = file_research.get('news_research')
            view.data['candidate_research_pack'] = file_research.get('candidate_research_pack')
            view.data['universe_scope'] = file_research.get('universe_scope')
            view.data['research_input_manifest'] = {
                'variant_id': file_research['variant_id'],
                'path': file_research['path'],
                'information_cutoff': file_research['information_cutoff'],
                'file_sha256': file_research['file_sha256'],
                'missing_files': file_research['missing_files'],
            }
        view.evaluation_start_override = self.data.get('evaluation_start_known')
        view.evaluation_end_override = self.data.get('evaluation_end_known')
        view.fingerprint = digest(visible)
        # Aliases exist only in this rendering view. Stored hashes/snapshots name
        # the actual standalone variant file, not the old shared template.
        view.templates = {
            f'strategies/{self.series}/ai_input_template.md': runtime_prompt,
            f'strategies/{self.series}/variants/{self.variant}.md': ''}
        request = BaseSimulation.prepare(view, day)
        if not request.get('completed'):
            view.store.write(f"requests/{day}/time_travel.json", travel)
            if research_state is not None:
                view.store.write(f"requests/{day}/research_state.json", research_state)
            if file_research is not None:
                view.store.write(
                    f"requests/{day}/research_input_manifest.json",
                    view.data['research_input_manifest'])
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
            if order.get('side') == 'BUY' and request.get('decision_research_bundle') is not None:
                preflight = buy_research_preflight(
                    request.get('decision_research_bundle'), order['symbol'])
                require(preflight['ready'],
                        'BUY research preflight failed: ' + ','.join(preflight['reasons']))
            rows = request['market'].get(order['symbol'], [])
            require(bool(rows), 'no point-in-time quote for selected stock')
            last = rows[-1]
            require(number(order['reference_price_cny']) == number(last['close']), 'reference quote does not match visible history')
            require(order['quote_source'] == last['source'], 'reference quote source is not in input')
            require(order['quote_time'] == request['context']['information_cutoff'], 'reference quote must use the replay cutoff')
