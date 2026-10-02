"""Live FORMAL Paper-Trading preparation and cutover parity checks.

This module does not fetch live data by itself and does not enable formal execution.
It consumes a verified LIVE_SNAPSHOT and the same full variant prompt / AI decision
contract / paper_core used by historical simulation.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path

from .paper_core import execute_single_order, validate_decision_contract
from .research_state import load_formal_state
from .sim_data import number
from .simulation import digest, holding_table, require
from .variant_prompts import variant_root, read as read_prompt_json, sha


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _source_commit(repo):
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, timeout=3, text=True,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "UNCOMMITTED_LOCAL_WORKSPACE"


def selected_prompt(root, scope):
    """Return the exact prompt text/version for SIMULATION or FORMAL."""
    root = Path(root)
    pointer_name = "simulation_prompt.json" if scope == "SIMULATION" else "formal_prompt.json"
    pointer = root / pointer_name
    if pointer.exists():
        p = read_json(pointer)
        chosen = (root / p["path"]).resolve()
        require(chosen.is_relative_to(root.resolve()), "prompt pointer escapes variant")
        text = chosen.read_text(encoding="utf-8")
        require(sha(text) == p["sha256"], "prompt pointer hash mismatch")
        return text, p
    text = (root / "prompt.md").read_text(encoding="utf-8")
    return text, {"version": "v000", "path": "prompt.md", "sha256": sha(text),
                  "scope": scope + "_BASELINE"}


def cutover_readiness(repo, variant):
    """Check whether tested and formal prompt versions are identical.

    This never enables formal execution and never copies simulation holdings/P&L.
    """
    repo = Path(repo).resolve()
    root = variant_root(repo, variant)
    sim_text, sim = selected_prompt(root, "SIMULATION")
    formal_text, formal = selected_prompt(root, "FORMAL")
    index = read_json(repo / "strategies/index.json")
    reg = next(x for x in index.get("variants", []) if x["variant_id"] == variant)
    holdings = read_json(root / "holdings.json")
    checks = {
        "same_prompt_hash": sha(sim_text) == sha(formal_text),
        "formal_global_enabled": index.get("formal_execution_enabled") is True,
        "variant_enabled": reg.get("enabled") is True,
        "variant_status_ready": reg.get("status") in {"READY", "ACTIVE"},
        "formal_account_initialized": holdings.get("status") != "NOT_INITIALIZED",
        "formal_account_execution_enabled": holdings.get("_meta", {}).get("execution_enabled") is True,
    }
    return {
        "variant_id": variant,
        "simulation_prompt_version": sim["version"],
        "formal_prompt_version": formal["version"],
        "checks": checks,
        "ready": all(checks.values()),
        "note": "Prompt promotion, account initialization and execution authorization are separate. "
                "Simulation holdings/P&L are never promoted.",
    }


def validate_live_snapshot(snapshot, *, max_quote_age_seconds=300):
    require(snapshot.get("kind") == "LIVE_SNAPSHOT", "formal mode requires LIVE_SNAPSHOT")
    as_of = datetime.fromisoformat(snapshot["as_of"])
    require(as_of.tzinfo is not None, "as_of must be timezone-aware")
    require(snapshot.get("market_date") == as_of.date().isoformat(), "market date/as_of mismatch")
    # Continuous trading windows only for current MVP. Auction support requires its own adapter.
    clock = as_of.timetz().replace(tzinfo=None)
    in_session = time(9, 30) <= clock <= time(11, 30) or time(13, 0) <= clock <= time(15, 0)
    require(in_session, "not in supported continuous-trading session")
    quotes = snapshot.get("quotes")
    require(isinstance(quotes, dict) and quotes, "quotes missing")
    for symbol, q in quotes.items():
        qt = datetime.fromisoformat(q["quote_time"])
        require(qt.tzinfo is not None and qt <= as_of, "future or naive quote time")
        require((as_of - qt).total_seconds() <= max_quote_age_seconds, "stale formal quote")
        require(number(q["price"]) > 0 and q.get("source"), "invalid formal quote")
        require(q.get("limit_up") is not None and q.get("limit_down") is not None,
                "formal quote missing price-limit metadata")
    for item in snapshot.get("evidence", []):
        pt = datetime.fromisoformat(item["published_at"])
        require(pt.tzinfo is not None and pt <= as_of, "future formal evidence")
        require(item.get("source"), "formal evidence missing source")
    return True


class FormalPaperSession:
    """Prepare/validate FORMAL Paper Trading with the same contract as simulation.

    The current public project keeps formal execution disabled. execute_preview()
    returns an in-memory post-trade state only; persistence must remain gated by
    cutover_readiness() and a future explicitly-authorized formal writer.
    """
    def __init__(self, repo, series, variant):
        self.repo = Path(repo).resolve()
        self.series, self.variant = series, variant
        root = variant_root(self.repo, variant)
        require(root.parent.parent.name == series, "variant/series mismatch")
        self.root = root
        self.index = read_json(self.repo / "strategies/index.json")
        self.spec = next(x for x in self.index["strategies"] if x["strategy_id"] == series)
        self.registry = next(x for x in self.index["variants"] if x["variant_id"] == variant)
        self.prompt, self.prompt_pointer = selected_prompt(root, "FORMAL")
        self.holdings_path = root / "holdings.json"
        self.source_commit = _source_commit(self.repo)
        self.runtime_buy_symbols = None
        self.runtime_allowed_symbols = None
        fee_file = self.repo / "config/default.json"
        cfg = read_json(fee_file) if fee_file.exists() else {}
        self.fees = {k: number(cfg.get(k, v)) for k, v in {
            "commission_rate": "0.00025", "min_commission": "5",
            "stamp_duty_sell_rate": "0.0005", "transfer_fee_rate": "0.00001",
        }.items()}

    def check_symbol(self, symbol):
        require(re.fullmatch(r"\d{6}\.(SH|SZ)", symbol or "") is not None, "bad symbol")
        require(not symbol.startswith(("688", "689", "300", "301")), "excluded board")
        if self.spec["type"] == "FIXED":
            require(symbol in self.spec["symbols"], "outside fixed universe")
        elif self.runtime_allowed_symbols is not None:
            require(symbol in self.runtime_allowed_symbols,
                    "outside current AI_SELECT candidates and holdings")

    def prepare(self, snapshot):
        validate_live_snapshot(snapshot)
        state = read_json(self.holdings_path)
        require(state.get("status") != "NOT_INITIALIZED", "formal account not initialized")
        require(state.get("_meta", {}).get("mode") == "FORMAL", "not a formal account")
        as_of = snapshot["as_of"]
        day = snapshot["market_date"]
        before = copy.deepcopy(state)
        held_symbols = {p["symbol"] for p in before["positions"]}
        research_state = None
        authorized_universe = self.spec.get("symbols", list(snapshot["quotes"]))
        if self.spec["type"] == "AI_SELECT":
            pack = snapshot.get("candidate_research_pack")
            scope = snapshot.get("universe_scope")
            require(isinstance(pack, dict) and pack.get("kind") == "AI_SELECT_DEEP_RESEARCH_PACK",
                    "AI_SELECT formal preview requires a bounded candidate research pack")
            require(isinstance(scope, dict), "AI_SELECT formal preview requires universe_scope")
            candidates = set(scope.get("authorized_symbols") or [])
            if not candidates:
                candidates = {x.get("symbol") for x in pack.get("candidates", []) if x.get("symbol")}
            require(bool(candidates), "AI_SELECT candidate universe is empty")
            require(candidates <= set(snapshot["quotes"]), "candidate quote missing from live snapshot")
            require(candidates <= set(snapshot.get("instruments", {})),
                    "candidate instrument metadata missing from live snapshot")
            self.runtime_buy_symbols = set(candidates)
            self.runtime_allowed_symbols = set(candidates) | held_symbols
            authorized_universe = {
                "buy_candidates": sorted(candidates),
                "existing_holdings_allowed_for_sell": sorted(held_symbols),
                "coverage": scope.get("coverage"),
                "not_full_a_share_claim": scope.get("not_full_a_share_claim", True),
            }
            research_state = load_formal_state(self.repo, self.series, self.variant)
        else:
            self.runtime_buy_symbols = None
            self.runtime_allowed_symbols = None
        for p in before["positions"]:
            # Existing holdings remain sellable even if they fall out of today's candidate pool.
            self.check_symbol(p["symbol"])
        context = {
            "mode": "FORMAL", "strategy_id": self.series, "variant_id": self.variant,
            "run_id": f"formal-{self.variant}-{day}",
            "decision_id": f"formal-{self.variant}-{day}",
            "date": day, "decision_time": as_of, "information_cutoff": as_of,
            "execution_time": as_of, "timezone": "Asia/Shanghai",
            "execution_basis": "VERIFIED_CURRENT_QUOTE_PAPER_FILL",
            "input_revision": state["_meta"]["revision"], "input_commit": self.source_commit,
            "input_snapshot_sha256": digest({"holdings": state, "snapshot": snapshot,
                                             "prompt_sha256": sha(self.prompt)}),
            "account_path": str(self.holdings_path.relative_to(self.repo)),
            "authorization": "FORMAL Paper Trading only; no brokerage order.",
            "evaluation_start": self.index.get("evaluation_start"),
            "evaluation_end": self.index.get("evaluation_end"),
            "settlement_note": "sellable_quantity comes from persisted T+1 account state",
            "data_kind": "LIVE_SNAPSHOT", "fidelity": snapshot.get("fidelity", "LIVE_PAPER"),
        }
        market = {
            s: [{
                "date": day, "close": q["price"], "source": q["source"],
                "quote_time": q["quote_time"],
            }]
            for s, q in snapshot["quotes"].items()
        }
        prior = snapshot.get("previous_decision_summary", "正式账户当前状态")
        tools = {
            "current_quotes": snapshot["quotes"],
            "evidence": snapshot.get("evidence", []),
            "candidate_research_pack": snapshot.get("candidate_research_pack"),
            "research_state": research_state,
            "universe_scope": snapshot.get("universe_scope"),
            "tools": snapshot.get("tools", "verified live-data adapter"),
            "limitations": snapshot.get("limitations", []),
            "fundamentals_news_coverage": snapshot.get("fundamentals_news_coverage",
                                                        "as supplied by live research layer"),
        }
        fields = {
            "RUN_CONTEXT": json.dumps(context, ensure_ascii=False, indent=2),
            "HOLDINGS_JSON": json.dumps(before, ensure_ascii=False, indent=2),
            "HOLDINGS_TABLE_ROWS": holding_table(before),
            "PREVIOUS_DECISION_SUMMARY": prior,
            "AUTHORIZED_UNIVERSE": json.dumps(
                authorized_universe, ensure_ascii=False, indent=2),
            "EVIDENCE_AND_TOOL_CONTEXT": json.dumps(tools, ensure_ascii=False, indent=2),
        }
        prompt = self.prompt
        for name, value in fields.items():
            prompt = prompt.replace("{{" + name + "}}", value)
        require(not re.search(r"\{\{[^}]+\}\}", prompt), "unresolved formal prompt variable")
        return {
            "context": context, "holdings": before, "market": market,
            "evidence": snapshot.get("evidence", []), "prompt": prompt,
            "prompt_sha256": digest(prompt), "source_holdings": state,
            "live_snapshot": snapshot,
        }

    def validate_decision(self, response, request):
        def quote_validator(order, req):
            q = req["live_snapshot"]["quotes"].get(order["symbol"])
            require(q is not None, "selected symbol has no live quote")
            if self.spec["type"] == "AI_SELECT":
                if order.get("side") == "BUY":
                    require(order["symbol"] in (self.runtime_buy_symbols or set()),
                            "AI_SELECT buy is outside today's bounded candidate pool")
                elif order.get("side") == "SELL":
                    held = {p["symbol"] for p in req["holdings"]["positions"]}
                    require(order["symbol"] in held, "AI_SELECT sell is not a current holding")
            require(number(order["reference_price_cny"]) == number(q["price"]),
                    "reference price must match current verified quote")
            require(order["quote_time"] == q["quote_time"], "reference quote time mismatch")
            require(order["quote_source"] == q["source"], "reference quote source mismatch")
        return validate_decision_contract(response, request, self.check_symbol,
                                          quote_validator=quote_validator)

    def execute_preview(self, response, request):
        """Use exactly the shared paper_core accounting, without persisting FORMAL state."""
        self.validate_decision(response, request)
        order = response.get("order_proposal")
        if order:
            q = request["live_snapshot"]["quotes"][order["symbol"]]
            quote = {
                "price": q["price"], "source": q["source"], "quote_time": q["quote_time"],
                "suspended": q.get("suspended", False), "limit_up": q["limit_up"],
                "limit_down": q["limit_down"],
            }
            instrument = request["live_snapshot"]["instruments"][order["symbol"]]
        else:
            quote = {"price": "1.00", "source": "NO_TRADE",
                     "quote_time": request["context"]["execution_time"],
                     "suspended": False, "limit_up": "999999.99", "limit_down": "0.01"}
            instrument = {"name": "NO_TRADE", "lot_size": 100}
        return execute_single_order(
            request["holdings"], response, quote, instrument, self.fees,
            mode="FORMAL", execution_basis="VERIFIED_CURRENT_QUOTE_PAPER_FILL",
            execution_time=request["context"]["execution_time"],
        )
