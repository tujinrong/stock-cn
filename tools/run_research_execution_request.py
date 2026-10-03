#!/usr/bin/env python3
"""Check whether a locked research-only decision can now be settled.

Fetches only bounded candidate/holding history transiently. If no real next session
is available through check_through, records WAITING and does not fabricate a fill.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from stock_cn.research_execution import settle_locked_research_decision
from stock_cn.simulation import Store, identifier, read_json, require
from stock_cn.universe import fetch_candidate_history


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--request", required=True)
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    spec = load(repo / args.request)
    test_id = identifier(spec["test_id"])
    variant = spec["variant_id"]
    target = spec["target_date"]
    check_through = spec["check_through"]
    date.fromisoformat(target)
    date.fromisoformat(check_through)
    require(check_through >= target, "check_through cannot precede target")

    root = repo / "runs/research-decisions" / test_id / variant / target
    request = read_json(root / "request.json")
    lock = read_json(root / "decision.lock.json")
    require(lock.get("execution_status") == "WAITING_FOR_REAL_NEXT_SESSION_DATA",
            "research decision is not pending next-session execution")

    symbols = set(request.get("market", {}))
    symbols |= {p["symbol"] for p in request["holdings"].get("positions", [])}
    require(bool(symbols), "no research-decision symbols to check")
    max_symbols = int(spec.get("max_symbols", 12))
    require(len(symbols) <= max_symbols, "execution-check symbol budget exceeded")

    names = {}
    pack = request.get("candidate_research_pack") or {}
    for item in pack.get("candidates", []):
        if item.get("symbol"):
            names[item["symbol"]] = item.get("name") or item["symbol"]
    for p in request["holdings"].get("positions", []):
        names[p["symbol"]] = p.get("name") or p["symbol"]

    seed = {
        "kind": "BOUNDED_CANDIDATE_SEED",
        "purpose": "LOCKED_RESEARCH_DECISION_EXECUTION_CHECK",
        "count": len(symbols),
        "rows": [
            {"symbol": s, "name": names.get(s, s), "risk_tags": []}
            for s in sorted(symbols)
        ],
        "source": "locked research-decision request",
        "survivorship_warning": None,
    }
    start = (date.fromisoformat(target) - timedelta(days=20)).isoformat()
    data, attempts = fetch_candidate_history(
        seed, start, check_through, max_symbols=max_symbols
    )
    require(data is not None, "execution-check market sources failed")
    result = settle_locked_research_decision(
        repo, test_id, variant, target, data,
        check_through=check_through,
    )
    Store(root).write(f"execution-source-probes/{check_through}.json", {
        "test_id": test_id,
        "variant_id": variant,
        "target_date": target,
        "check_through": check_through,
        "attempts": attempts,
        "raw_market_data_persisted": False,
        "result_status": result["status"],
        "formal_execution": False,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
