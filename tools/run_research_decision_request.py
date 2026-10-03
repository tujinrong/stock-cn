#!/usr/bin/env python3
"""Prepare a research-only time-travel AI decision request from repository research inputs.

Market history is fetched transiently and is not persisted as a raw database.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from stock_cn.research_decision import prepare_research_only_request
from stock_cn.simulation import Store, dumps, identifier, read_json, require
from stock_cn.universe import fetch_candidate_history
from stock_cn.variant_prompts import variant_root


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
    date.fromisoformat(target)

    research_root = repo / "research-inputs" / variant / target
    manifest = read_json(research_root / "manifest.json")
    require(manifest.get("mode") == "SIMULATION",
            "research decision request requires SIMULATION research inputs")
    scope = read_json(research_root / "universe-scope.json")
    authorized = list(scope.get("authorized_symbols") or [])
    require(bool(authorized), "research decision authorized universe is empty")

    pack = read_json(research_root / "candidate-research-pack.json")
    by_symbol = {
        x["symbol"]: x for x in pack.get("candidates", [])
        if x.get("symbol")
    }

    # Include any assumed opening holdings even if they are no longer buy candidates.
    init = read_json(variant_root(repo, variant) / "init.json")
    requested = []
    for symbol in authorized:
        item = by_symbol.get(symbol, {})
        requested.append({
            "symbol": symbol,
            "name": item.get("name") or symbol,
            "price_cny": (item.get("seed_snapshot") or {}).get("price_cny"),
            "change_pct": (item.get("seed_snapshot") or {}).get("change_pct"),
            "amount_cny": (item.get("seed_snapshot") or {}).get("amount_cny"),
            "risk_tags": item.get("risk_tags", []),
        })
    for stock in init.get("stocks", []):
        symbol = stock["symbol"]
        if symbol not in {x["symbol"] for x in requested}:
            requested.append({
                "symbol": symbol,
                "name": stock.get("name") or symbol,
                "risk_tags": [],
            })

    max_symbols = int(spec.get("max_symbols", 12))
    require(len(requested) <= max_symbols,
            "research decision candidate count exceeds bounded history budget")
    seed = {
        "kind": "BOUNDED_CANDIDATE_SEED",
        "purpose": pack.get("purpose"),
        "count": len(requested),
        "rows": requested,
        "source": pack.get("seed_source"),
        "source_provider": pack.get("seed_provider"),
        "fallback_used": pack.get("seed_fallback_used", False),
        "survivorship_warning": pack.get("survivorship_warning"),
    }
    start = (date.fromisoformat(target) - timedelta(days=399)).isoformat()
    data, attempts = fetch_candidate_history(
        seed, start, target, max_symbols=max_symbols
    )
    require(data is not None, "candidate history sources failed")
    require(target in data["sessions"], "target-date market data missing")
    data["candidate_research_pack"] = pack
    data["universe_scope"] = scope
    data["limitations"] = list(data.get("limitations", [])) + [
        "Research-only decision: no next-session execution price was requested or fabricated.",
        "Financial/news research is loaded from validated GitHub research-input files.",
    ]

    request = prepare_research_only_request(
        repo, variant, test_id, data, target
    )
    root = repo / "runs" / "research-decisions" / test_id / variant / target
    store = Store(root)
    store.write("source-probe.json", {
        "test_id": test_id,
        "variant_id": variant,
        "target_date": target,
        "history_requested_start": start,
        "history_requested_end": target,
        "attempts": attempts,
        "raw_market_data_persisted": False,
        "execution_data_requested": False,
        "formal_execution": False,
    })
    summary = {
        "test_id": test_id,
        "variant_id": variant,
        "target_date": target,
        "prompt_version": request["prompt_pointer"]["version"],
        "authorized_symbols": authorized,
        "research_input_path": request["research_input_manifest"]["path"]
            if request.get("research_input_manifest") else None,
        "decision_research_coverage": (
            request["decision_research_bundle"]["coverage"]
            if request.get("decision_research_bundle") else None
        ),
        "execution_status": request["execution_status"],
        "formal_execution": False,
        "raw_market_data_persisted": False,
    }
    store.write("summary.json", summary)
    print(dumps(summary))


if __name__ == "__main__":
    main()
