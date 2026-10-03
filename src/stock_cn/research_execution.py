"""Deferred execution of an already-locked research-only decision.

The AI decision is immutable. This module may look at future execution data only
after the decision lock exists. It either reports WAITING or executes exactly the
first supplied market session after the target date using the shared paper core.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from .paper_core import execute_single_order
from .sim_data import number, validate_dataset
from .simulation import Store, digest, money, read_json, require
from .variant_prompts import variant_root


def _root(repo, test_id, variant, target_date):
    return (
        Path(repo).resolve() / "runs" / "research-decisions" /
        test_id / variant / target_date
    )


def _fees(repo):
    p = Path(repo) / "config/default.json"
    cfg = read_json(p) if p.exists() else {}
    return {
        k: number(cfg.get(k, v)) for k, v in {
            "commission_rate": "0.00025",
            "min_commission": "5",
            "stamp_duty_sell_rate": "0.0005",
            "transfer_fee_rate": "0.00001",
        }.items()
    }


def _load_locked(repo, test_id, variant, target_date):
    root = _root(repo, test_id, variant, target_date)
    request = read_json(root / "request.json")
    decision = read_json(root / "decision.json")
    lock = read_json(root / "decision.lock.json")
    require(lock["prompt_sha256"] == request["prompt_sha256"],
            "research-only prompt changed after decision lock")
    require(lock["decision_sha256"] == digest(decision),
            "research-only decision changed after lock")
    require(lock.get("future_execution_data_seen") is False,
            "decision lock unexpectedly contains future execution data")
    return root, request, decision, lock


def settle_locked_research_decision(
    repo,
    test_id,
    variant,
    target_date,
    data,
    *,
    check_through,
):
    """Execute the locked decision only if a real next session exists in data."""
    repo = Path(repo).resolve()
    validate_dataset(data)
    root, request, decision, lock = _load_locked(
        repo, test_id, variant, target_date
    )
    store = Store(root)

    settled_path = root / "settlement.json"
    if settled_path.exists():
        return read_json(settled_path)

    sessions = [
        d for d in data["sessions"]
        if target_date < d <= check_through
    ]
    if not sessions:
        attempt = {
            "status": "WAITING_FOR_REAL_NEXT_SESSION_DATA",
            "test_id": test_id,
            "variant_id": variant,
            "target_date": target_date,
            "check_through": check_through,
            "decision_sha256": lock["decision_sha256"],
            "future_execution_data_seen_by_decision": False,
            "formal_state_changed": False,
        }
        store.write(f"execution-attempts/{check_through}.json", attempt)
        return attempt

    execution_day = sessions[0]
    after = copy.deepcopy(request["holdings"])
    order = decision.get("order_proposal")
    if order:
        symbol = order["symbol"]
        require(symbol in data["bars"].get(execution_day, {}),
                "first next-session execution bar missing for selected symbol")
        quote_bar = data["bars"][execution_day][symbol]
        quote = {
            "price": quote_bar["open"],
            "source": quote_bar["source"],
            "quote_time": f"{execution_day}T09:30:00+08:00",
            "suspended": quote_bar.get("suspended", False),
            "limit_up": quote_bar.get("limit_up"),
            "limit_down": quote_bar.get("limit_down"),
        }
        instrument = data["instruments"].get(symbol)
        require(instrument is not None, "execution instrument metadata missing")
    else:
        quote = {
            "price": "1.00",
            "source": "NO_TRADE",
            "quote_time": f"{execution_day}T09:30:00+08:00",
            "suspended": False,
            "limit_up": "999999.99",
            "limit_down": "0.01",
        }
        instrument = {"name": "NO_TRADE", "lot_size": 100}

    after, execution = execute_single_order(
        request["holdings"],
        decision,
        quote,
        instrument,
        _fees(repo),
        mode="SIMULATION",
        execution_basis="LOCKED_RESEARCH_DECISION_NEXT_REAL_SESSION_OPEN",
        execution_time=f"{execution_day}T09:30:00+08:00",
    )

    after["date"] = execution_day
    after["_meta"] = copy.deepcopy(after.get("_meta", {}))
    after["_meta"].update({
        "valuation_time": f"{execution_day}T15:00:00+08:00",
        "last_decision_date": target_date,
        "locked_research_decision": True,
        "execution_day": execution_day,
    })

    value = number(after["cash_cny"])
    for p in after["positions"]:
        require(p["symbol"] in data["bars"].get(execution_day, {}),
                "execution-day close missing for held symbol")
        close = number(data["bars"][execution_day][p["symbol"]]["close"])
        p["valuation_price_cny"] = money(close)
        value += close * p["quantity"]
    after["total_equity_cny"] = money(value)

    settlement = {
        "status": "SETTLED",
        "test_id": test_id,
        "variant_id": variant,
        "target_date": target_date,
        "execution_date": execution_day,
        "check_through": check_through,
        "decision_sha256": lock["decision_sha256"],
        "prompt_sha256": lock["prompt_sha256"],
        "execution": execution,
        "holdings_after": after,
        "future_execution_data_seen_by_decision": False,
        "formal_state_changed": False,
        "continuation_ready": execution["status"] in {"FILLED", "NO_TRADE", "REJECTED"},
        "note": (
            "Decision was locked before execution data existed. "
            "Settlement used only the first supplied real session after target date."
        ),
    }
    store.write("execution.json", execution)
    store.write("holdings_after_execution.json", after)
    store.write("settlement.json", settlement)
    store.write("continuation.json", {
        "variant_id": variant,
        "source_test_id": test_id,
        "source_target_date": target_date,
        "execution_date": execution_day,
        "state": after,
        "decision_sha256": lock["decision_sha256"],
        "execution_status": execution["status"],
        "formal_execution": False,
    })
    return settlement
