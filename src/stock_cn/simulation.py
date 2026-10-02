"""Simulation-only ledger and AI hand-off. No strategy scoring or brokerage API.

Events are authoritative; holdings and daily files are repairable projections.
Only strategies/<series>/simulations/<test_id>/<variant>/ can be written.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
import subprocess
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .sim_data import number, validate_dataset
from .paper_core import PaperCoreError, execute_single_order, validate_decision_contract


class ValidationError(ValueError):
    """Input is unsafe, stale, incomplete or incompatible with this simulation."""


def dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def digest(value):
    raw = value if isinstance(value, str) else dumps(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def money(value):
    return str(number(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,90}", value), "invalid path identifier")
    return value


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_account(state):
    require(state["_meta"]["mode"] == "SIMULATION", "formal state is not accepted")
    cash = number(state["cash_cny"])
    require(cash >= 0, "negative cash")
    seen, value = set(), cash
    for p in state["positions"]:
        q, a = p["quantity"], p["sellable_quantity"]
        require(p["symbol"] not in seen, "duplicate holding")
        seen.add(p["symbol"])
        require(integer(q) and integer(a) and 0 <= a <= q, "invalid quantity or T+1 availability")
        require(number(p["average_cost_cny"]) >= 0 and number(p["valuation_price_cny"]) > 0, "invalid valuation")
        value += q * number(p["valuation_price_cny"])
    require(money(value) == money(state["total_equity_cny"]), "equity does not reconcile")


def holding_table(state):
    rows = []
    total = number(state["total_equity_cny"])
    for p in state["positions"]:
        value = p["quantity"] * number(p["valuation_price_cny"])
        rows.append(f"| {p['symbol']} | {p['name']} | {p['quantity']} | {p['sellable_quantity']} | "
                    f"{p['average_cost_cny']} | {p['valuation_price_cny']} / {state['_meta']['valuation_time']} | "
                    f"{money(value)} / {value/total:.2%} |")
    return "\n".join(rows) or "| — | 无持仓 | 0 | 0 | — | — | 0 |"


def holdings_md(state):
    return (f"# 模拟持仓 {state['strategy_id']} / {state['_meta']['variant_id']}\n\n"
            f"日期：{state['date']}；总资产：{state['total_equity_cny']}；现金：{state['cash_cny']}。\n\n"
            "|代码|名称|股数|可卖|成本|估值/时间|市值/权重|\n|---|---|---:|---:|---:|---|---|\n"
            + holding_table(state) + "\n")


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, relative):
        p = (self.root / relative).resolve()
        require(p.is_relative_to(self.root.resolve()), "path escape")
        return p

    def write(self, relative, content):
        p = self.path(relative)
        p.parent.mkdir(parents=True, exist_ok=True)
        raw = content if isinstance(content, str) else dumps(content)
        fd, temp = tempfile.mkstemp(prefix=".pending-", dir=p.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, p)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    @contextmanager
    def lock(self):
        p = self.path(".account.lock")
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValidationError("account is busy; do not delete an active lock") from exc
        try:
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            yield
        finally:
            p.unlink(missing_ok=True)

    def events(self):
        result, previous = [], None
        for i, p in enumerate(sorted(self.path("events").glob("*.json")), 1):
            event = read_json(p)
            actual = event.pop("sha256", None)
            require(event["sequence"] == i and p.name == f"{i:06d}.json", "event sequence damaged")
            require(event["previous_hash"] == previous and digest(event) == actual, "event hash-chain damaged")
            assert_account(event["after"])
            if result:
                require(event["before"] == result[-1]["after"], "event/account continuity damaged")
            event["sha256"] = actual
            result.append(event)
            previous = actual
        return result

    def project(self, event):
        for path, value in event["documents"].items():
            self.write(path, value)
        self.write("holdings.json", event["after"])
        self.write("holdings.md", holdings_md(event["after"]))

    def commit(self, event_type, before, after, documents, details=None):
        history = self.events()
        seq = len(history) + 1
        require(before == (history[-1]["after"] if history else None), "stale account revision")
        after = copy.deepcopy(after)
        after["_meta"].update(revision=seq, last_event_id=f"{seq:06d}")
        assert_account(after)
        documents = copy.deepcopy(documents)
        # Event stores the final revision, not a half-updated projection.
        for k in list(documents):
            if k.endswith("holdings_after.json"):
                documents[k] = after
        event = {"sequence": seq, "type": event_type,
                 "previous_hash": history[-1]["sha256"] if history else None,
                 "before": before, "after": after, "documents": documents, "details": details or {}}
        event["sha256"] = digest(event)
        self.write(f"events/{seq:06d}.json", event)
        # Crash here is recoverable: the immutable event was committed first.
        self.project(event)
        return after

    def load(self):
        events = self.events()
        require(bool(events), "NOT_INITIALIZED")
        return copy.deepcopy(events[-1]["after"])

    def audit(self, repair=False):
        with self.lock():
            events = self.events()  # Never 'repair' damaged authoritative events.
            require(bool(events), "NOT_INITIALIZED")
            expected = {}
            for event in events:
                expected.update(event["documents"])
            expected["holdings.json"] = events[-1]["after"]
            expected["holdings.md"] = holdings_md(events[-1]["after"])
            broken = []
            for name, value in expected.items():
                text = value if isinstance(value, str) else dumps(value)
                p = self.path(name)
                if not p.exists() or p.read_text(encoding="utf-8") != text:
                    broken.append(name)
                    if repair:
                        self.write(name, value)
            report = {"event_count": len(events), "event_chain_valid": True,
                      "projection_errors": broken, "repaired": broken if repair else [],
                      "ok": not broken or repair,
                      "scope": "Only rebuild projections; never change trades, strategy or prices."}
            self.write("validation.json", report)
            return report


class Simulation:
    """Explicit daily replay. AI sees previous-close evidence; fills use next open.

    This is NOT an 11:00 replay. Daily data cannot reconstruct a historical 11:00 quote.
    """
    def __init__(self, repo, series, variant, test_id, data):
        self.repo = Path(repo).resolve()
        self.series, self.variant, self.test_id = map(identifier, (series, variant, test_id))
        index = read_json(self.repo / "strategies/index.json")
        matches = [x for x in index["strategies"] if x["strategy_id"] == series]
        require(len(matches) == 1, "unknown series")
        self.spec = matches[0]
        require(self.spec["type"] != "RESERVED" and variant in self.spec["variants"], "reserved/unknown variant")
        validate_dataset(data)
        self.data = copy.deepcopy(data)
        base = self.repo / "strategies" / series / "simulations"
        root = base / test_id / variant
        require(root.resolve().is_relative_to(base.absolute()), "simulation directory symlink escape")
        self.store = Store(root)
        self.init = read_json(self.repo / "strategies" / series / "init.json")
        self.templates = {}
        for relative in ("AGENTS.md", "strategies/common.md", f"strategies/{series}/prompt.md",
                         f"strategies/{series}/variants/{variant}.md", f"strategies/{series}/ai_input_template.md"):
            self.templates[relative] = (self.repo / relative).read_text(encoding="utf-8")
        fee_file = self.repo / "config/default.json"
        config = read_json(fee_file) if fee_file.exists() else {}
        self.fees = {k: number(config.get(k, v)) for k, v in {"commission_rate": "0.00025", "min_commission": "5", "stamp_duty_sell_rate": "0.0005", "transfer_fee_rate": "0.00001"}.items()}
        require(all(v >= 0 for v in self.fees.values()), "invalid negative fee")
        try:
            self.source_commit = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=3, text=True).strip()
        except (OSError, subprocess.SubprocessError):
            self.source_commit = "UNCOMMITTED_LOCAL_WORKSPACE"
        fingerprint_data = copy.deepcopy(self.data)
        fingerprint_data.pop("retrieved_at", None)
        self.fingerprint = digest({"init": self.init, "templates": self.templates, "fees": {k: str(v) for k, v in self.fees.items()},
                                   "dataset": fingerprint_data, "series_spec": self.spec})

    def bar(self, day, symbol):
        require(symbol in self.data["bars"].get(day, {}), f"missing {day} {symbol}; never forward-fill an execution price")
        return self.data["bars"][day][symbol]

    def initialize(self):
        with self.store.lock():
            if self.store.events():
                manifest = self.store.events()[0]["documents"]["manifest.json"]
                require(manifest["input_fingerprint"] == self.fingerprint, "inputs changed: use a new test_id")
                return self.store.load()
            day = self.data["sessions"][0]
            cash = number(self.init["initial_capital_cny"])
            positions = []
            if self.init["opening_method"] == "ASSUMED_EXISTING_PORTFOLIO":
                require(number(self.init["cash_weight"]) + sum(number(s["weight"]) for s in self.init["stocks"]) == 1,
                        "initial weights do not sum to one")
                for stock in self.init["stocks"]:
                    symbol = stock["symbol"]
                    self.check_symbol(symbol)
                    price = number(self.bar(day, symbol)["close"])
                    quantity = int(number(self.init["initial_capital_cny"]) * number(stock["weight"]) / price / 100) * 100
                    cash -= quantity * price
                    if quantity:
                        positions.append({"symbol": symbol, "name": self.data["instruments"][symbol]["name"],
                                          "quantity": quantity, "sellable_quantity": quantity,
                                          "average_cost_cny": money(price), "cost_basis_cny": money(quantity * price), "valuation_price_cny": money(price)})
            else:
                require(not self.init.get("stocks") or all(number(s.get("weight", 0)) == 0 for s in self.init["stocks"]),
                        "cash opening contains positive stock weights")
            state = {"strategy_id": self.series, "status": "SIMULATION", "date": day,
                     "initial_capital_cny": money(self.init["initial_capital_cny"]), "cash_cny": money(cash),
                     "total_equity_cny": money(self.init["initial_capital_cny"]), "positions": positions,
                     "_meta": {"schema_version": "0.4", "mode": "SIMULATION", "paper_only": True,
                               "variant_id": self.variant, "test_id": self.test_id, "revision": 0,
                               "valuation_time": f"{day}T15:00:00+08:00", "fees_cny": "0.00",
                               "last_decision_date": None, "data_kind": self.data["kind"]}}
            manifest = {"mode": "SIMULATION", "series": self.series, "variant": self.variant,
                        "test_id": self.test_id, "input_fingerprint": self.fingerprint, "source_commit": self.source_commit,
                        "fees": {k: str(v) for k, v in self.fees.items()},
                        "data_kind": self.data["kind"], "fidelity": self.data["fidelity"],
                        "execution_basis": "PREVIOUS_CLOSE_NEXT_OPEN_NOT_11AM", "sessions": self.data["sessions"],
                        "initialization": "ASSUMED_SETTLED_OPENING; not five same-day buys; no invented historic fees",
                        "limitations": self.data.get("limitations", []),
                        "source_version": " / ".join(sorted(set(b["source"] for b in self.data["bars"][day].values()))),
                        "template_sha256": {k: digest(v) for k, v in self.templates.items()}}
            return self.store.commit("OPENING_BALANCE", None, state,
                                     {"manifest.json": manifest, "init.snapshot.json": self.init,
                                      "templates.snapshot.json": self.templates})

    def check_symbol(self, symbol):
        require(symbol in self.data["instruments"], "instrument metadata missing")
        meta = self.data["instruments"][symbol]
        require(meta["board"] == "MAIN" and not symbol.startswith(("688", "689", "300", "301")), "excluded board")
        if self.spec["type"] == "FIXED":
            require(symbol in self.spec["symbols"], "outside fixed universe")

    def prepare(self, day):
        self.initialize()
        with self.store.lock():
            state = self.store.load()
            days = self.data["sessions"]
            require(day in days and days.index(day) > 0, "not a replay session")
            pos = days.index(day)
            final = self.store.path(f"daily/{day}/decision.json")
            if final.exists():
                return {"completed": True, "decision": read_json(final)}
            require(state["date"] == days[pos-1], "days must be processed in order; no skipped sessions")
            for p in state["positions"]:
                self.bar(day, p["symbol"])
            before = copy.deepcopy(state)
            for p in before["positions"]:
                p["sellable_quantity"] = p["quantity"]
            cutoff = f"{days[pos-1]}T15:00:00+08:00"
            context = {"mode": "SIMULATION", "strategy_id": self.series, "variant_id": self.variant,
                       "run_id": f"{self.test_id}-{self.variant}", "decision_id": f"{self.test_id}-{self.variant}-{day}",
                       "date": day, "decision_time": cutoff, "information_cutoff": cutoff,
                       "execution_time": f"{day}T09:30:00+08:00", "timezone": "Asia/Shanghai",
                       "execution_basis": "PREVIOUS_CLOSE_NEXT_OPEN_NOT_11AM",
                       "input_revision": state["_meta"]["revision"], "input_commit": self.source_commit,
                       "input_snapshot_sha256": self.fingerprint,
                       "account_path": str(self.store.root.relative_to(self.repo) / "holdings.json"),
                       "authorization": "Only this isolated simulation; not formal. DRAFT strategy may be tested.",
                       "evaluation_start": getattr(self, "evaluation_start_override", None),
                       "evaluation_end": getattr(self, "evaluation_end_override", None),
                       "settlement_note": "sellable_quantity is next-session availability, not same-day T+0",
                       "data_kind": self.data["kind"], "fidelity": self.data["fidelity"]}
            market = {s: [{"date": d, "close": self.data["bars"][d][s]["close"],
                           "source": self.data["bars"][d][s]["source"]}
                          for d in days[max(0, pos-10):pos] if s in self.data["bars"][d]]
                      for s in self.data["instruments"]}
            evidence = [x for x in self.data.get("evidence", [])
                        if datetime.fromisoformat(x["published_at"]) <= datetime.fromisoformat(cutoff)]
            prior = [e["details"].get("decision", {}).get("summary", "") for e in self.store.events()[-3:]]
            fields = {"RUN_CONTEXT": dumps(context), "HOLDINGS_JSON": dumps(before),
                      "HOLDINGS_TABLE_ROWS": holding_table(before), "PREVIOUS_DECISION_SUMMARY": "\n".join(prior) or "模拟期初",
                      "AUTHORIZED_UNIVERSE": dumps(self.spec.get("symbols", list(self.data["instruments"]))),
                      "EVIDENCE_AND_TOOL_CONTEXT": dumps({"historical_closes": market, "evidence": evidence,
                        "candidate_research_pack": self.data.get("candidate_research_pack"),
                        "universe_scope": self.data.get("universe_scope"),
                        "tools": "Use supplied point-in-time evidence only for this replay. No current-web lookahead.",
                        "limitations": self.data.get("limitations", []), "fundamentals_news_coverage": "only supplied evidence"})}
            template = self.templates[f"strategies/{self.series}/ai_input_template.md"]
            template += "\n\n## 本次选定变体原文\n" + self.templates[f"strategies/{self.series}/variants/{self.variant}.md"]
            template += "\n\n## 本次模式说明\n这是获授权的隔离模拟，不操作正式账户。未提供历史财务/新闻时应披露缺口。\n"
            template += "只输出一个符合契约的JSON对象；不使用当前网页补充历史未知资料。不要把流程测试称为投资有效性证明。\n"
            for name, value in fields.items():
                template = template.replace("{{" + name + "}}", value)
            require(not re.search(r"\{\{[^}]+\}\}", template), "unresolved prompt variable")
            request = {"context": context, "holdings": before, "market": market, "evidence": evidence,
                       "prompt": template, "prompt_sha256": digest(template), "source_holdings": state}
            folder = f"requests/{day}"
            existing = self.store.path(f"{folder}/request.json")
            if existing.exists():
                require(read_json(existing) == request, "request changed: use new test_id")
            self.store.write(f"{folder}/request.json", request)
            self.store.write(f"{folder}/ai_input.md", template)
            return request

    def validate_decision(self, response, request):
        try:
            return validate_decision_contract(response, request, self.check_symbol)
        except PaperCoreError as exc:
            raise ValidationError(str(exc)) from exc

    def apply(self, day, response, actual_prompt=None):
        request = self.prepare(day)
        if request.get("completed"):
            require(digest(request["decision"]) == digest(response), "conflicting duplicate decision")
            return read_json(self.store.path(f"daily/{day}/execution.json"))
        self.validate_decision(response, request)
        with self.store.lock():
            before = self.store.load()
            require(before == request["source_holdings"], "stale account; no concurrent overwrite")
            order = response["order_proposal"]
            quote = None
            instrument = None
            if order:
                symbol = order["symbol"]
                bar = self.bar(day, symbol)
                quote = {
                    "price": bar["open"],
                    "source": bar["source"],
                    "quote_time": request["context"]["execution_time"],
                    "suspended": bar.get("suspended", False),
                    "limit_up": bar.get("limit_up"),
                    "limit_down": bar.get("limit_down"),
                }
                instrument = self.data["instruments"][symbol]
            try:
                after, execution = execute_single_order(
                    request["holdings"], response,
                    quote or {"price": "1.00", "source": "NO_TRADE",
                              "quote_time": request["context"]["execution_time"],
                              "suspended": False, "limit_up": "999999.99", "limit_down": "0.01"},
                    instrument or {"name": "NO_TRADE", "lot_size": 100},
                    self.fees,
                    mode="SIMULATION",
                    execution_basis="PREVIOUS_CLOSE_NEXT_OPEN_NOT_11AM",
                    execution_time=request["context"]["execution_time"],
                )
            except PaperCoreError as exc:
                raise ValidationError(str(exc)) from exc
            execution["simulation_only"] = True
            after["date"] = day
            after["_meta"].update(last_decision_date=day, valuation_time=f"{day}T15:00:00+08:00")
            value = number(after["cash_cny"])
            for p in after["positions"]:
                close = self.bar(day, p["symbol"])["close"]
                p["valuation_price_cny"] = money(close)
                value += number(close) * p["quantity"]
            after["total_equity_cny"] = money(value)
            summary = (f"# {day} {self.variant} 隔离模拟\n\n数据：{self.data['kind']}；成交口径：前收信息 / 次日开盘。\n\n"
                       f"判断：{response['action']}；结果：{execution['status']}。\n\n{response['summary']}\n\n"
                       f"期末总资产：{after['total_equity_cny']}；现金：{after['cash_cny']}。\n\n"
                       "测试数据或脚本决定不证明AI投资有效；完整限制见manifest.json。\n")
            prefix = f"daily/{day}"
            documents = {f"{prefix}/ai_input.md": actual_prompt or request["prompt"], f"{prefix}/holdings_before.json": request["holdings"],
                         f"{prefix}/decision.json": response, f"{prefix}/execution.json": execution,
                         f"{prefix}/holdings_after.json": after, f"{prefix}/summary.md": summary,
                         f"{prefix}/research.json": {"evidence": response["evidence"], "data_gaps": response["data_gaps"]},
                         f"{prefix}/closing.json": {"date": day, "total_equity_cny": after["total_equity_cny"],
                                                   "cash_cny": after["cash_cny"], "valuation_time": after["_meta"]["valuation_time"],
                                                   "data_kind": self.data["kind"]}}
            self.store.commit("DAY_COMPLETED", before, after, documents, {"decision": response, "execution": execution})
            return execution

    def run_day(self, day, agent, repairs=1):
        require(integer(repairs) and 0 <= repairs <= 2, "at most two format-repair attempts")
        request = self.prepare(day)
        if request.get("completed"):
            return read_json(self.store.path(f"daily/{day}/execution.json"))
        errors = []
        for attempt in range(repairs + 1):
            attempt_request = copy.deepcopy(request)
            if errors:
                attempt_request["prompt"] += "\n\n## 同一次决策的校验反馈\n" + dumps(errors) + "修正输出，不改变模式或放宽约束。\n"
            self.store.write(f"requests/{day}/attempts/{attempt:02d}-input.md", attempt_request["prompt"])
            response = agent.decide(attempt_request, list(errors))
            self.store.write(f"requests/{day}/attempts/{attempt:02d}.json", {"response": response, "feedback": errors})
            try:
                if isinstance(response, str):
                    text = response.strip()
                    if text.startswith("```json") and text.endswith("```"):
                        text = text[7:-3].strip()
                    response = json.loads(text)
                self.validate_decision(response, request)
                break
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(str(exc))
                if attempt == repairs:
                    raise ValidationError("AI validation exhausted: " + "; ".join(errors)) from exc
        # Trading-rule rejection is FINAL that day; never try a second stock/order.
        return self.apply(day, response, actual_prompt=attempt_request["prompt"])

    def report(self):
        events = self.store.events()
        require(bool(events), "NOT_INITIALIZED")
        initial = number(events[0]["after"]["total_equity_cny"])
        peak, drawdown = initial, Decimal(0)
        for e in events:
            value = number(e["after"]["total_equity_cny"])
            peak = max(peak, value)
            drawdown = max(drawdown, 1 - value / peak)
        state = events[-1]["after"]
        result = {"variant": self.variant, "test_id": self.test_id, "data_kind": self.data["kind"],
                  "fidelity": self.data["fidelity"], "completed_days": len(events)-1,
                  "requested_days": len(self.data["sessions"])-1, "complete": len(events) == len(self.data["sessions"]),
                  "initial_equity_cny": money(initial), "final_equity_cny": state["total_equity_cny"],
                  "net_pnl_cny": money(number(state["total_equity_cny"]) - initial),
                  "return_pct": str((number(state["total_equity_cny"]) / initial - 1) * 100),
                  "max_daily_drawdown_pct": str(drawdown * 100), "fees_cny": state["_meta"]["fees_cny"],
                  "fills": sum(e["details"].get("execution", {}).get("status") == "FILLED" for e in events),
                  "limitations": self.data.get("limitations", []), "not_investment_validation": True}
        self.store.write("report.json", result)
        self.store.write("report.md", "# 模拟验证报告（不是投资成绩）\n\n```json\n" + dumps(result) + "```\n")
        return result
