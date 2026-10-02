#!/usr/bin/env python3
"""Bounded current-universe source probe for AI_SELECT infrastructure.

Persists compact candidate/research summaries, never the full raw market feed.
Not a formal trading run and not a recommendation.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from stock_cn.simulation import Store, dumps, identifier
from stock_cn.time_travel import symbol_snapshot
from stock_cn.universe import (
    bounded_prefilter,
    build_deep_research_pack,
    fetch_candidate_history,
    fetch_live_universe,
    update_abnormal_drop_watchlist,
)


def compact_seed(seed):
    return {
        "kind": seed["kind"],
        "purpose": seed["purpose"],
        "count": seed["count"],
        "max_candidates": seed["max_candidates"],
        "source_retrieved_at": seed["source_retrieved_at"],
        "source": seed["source"],
        "source_provider": seed.get("source_provider"),
        "fallback_used": seed.get("fallback_used", False),
        "primary_failure": seed.get("primary_failure"),
        "risk_tag_policy": seed.get("risk_tag_policy"),
        "not_a_recommendation": True,
        "survivorship_warning": seed["survivorship_warning"],
        "rows": seed["rows"],
    }


def probe_history(seed, purpose, start, end, *, max_symbols=5):
    tiny = dict(seed)
    tiny["rows"] = seed["rows"][:max_symbols]
    tiny["count"] = len(tiny["rows"])
    data, attempts = fetch_candidate_history(
        tiny, start, end, max_symbols=max_symbols
    )
    if data is None:
        return {
            "verified": False, "attempts": attempts, "snapshots": [],
            "research_pack": None, "watchlist": None,
        }
    cutoff = data["sessions"][-1]
    snaps = [symbol_snapshot(data, s, cutoff) for s in data["instruments"]]
    pack = build_deep_research_pack(
        tiny, data, cutoff, purpose, max_candidates=min(max_symbols, 12)
    )
    watchlist = (
        update_abnormal_drop_watchlist(None, tiny, data, cutoff, max_entries=max(10, max_symbols))
        if purpose == "ABNORMAL_DROP" else None
    )
    return {
        "verified": True,
        "attempts": attempts,
        "history_start": data["sessions"][0],
        "history_end": cutoff,
        "candidate_count": len(data["instruments"]),
        "snapshots": snaps,
        "research_pack": pack,
        "watchlist": watchlist,
        "limitations": data["limitations"],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--probe-id", required=True)
    p.add_argument("--candidate-limit", type=int, default=30)
    p.add_argument("--history-sample", type=int, default=5)
    args = p.parse_args()
    identifier(args.probe_id)
    repo = Path(args.repo).resolve()

    now_cn = datetime.now(ZoneInfo("Asia/Shanghai"))
    history_end = now_cn.date().isoformat()
    history_start = (now_cn.date() - timedelta(days=399)).isoformat()

    snap = fetch_live_universe()
    low = bounded_prefilter(snap, "LOW_RECOVERY", max_candidates=args.candidate_limit)
    drop = bounded_prefilter(snap, "ABNORMAL_DROP", max_candidates=args.candidate_limit)
    low_hist = probe_history(
        low, "LOW_RECOVERY", history_start, history_end,
        max_symbols=args.history_sample
    )
    drop_hist = probe_history(
        drop, "ABNORMAL_DROP", history_start, history_end,
        max_symbols=args.history_sample
    )

    root = repo / "runs/research/universe" / args.probe_id
    store = Store(root)
    store.write("summary.json", {
        "probe_id": args.probe_id,
        "market_timezone": "Asia/Shanghai",
        "history_requested_start": history_start,
        "history_requested_end": history_end,
        "provider_eligible_count": snap["eligible_count"],
        "provider_total_rows": snap["total_provider_rows"],
        "source": snap["source"],
        "source_provider": snap.get("source_provider"),
        "fallback_used": snap.get("fallback_used", False),
        "primary_failure": snap.get("primary_failure"),
        "source_pages": snap.get("source_pages"),
        "retrieved_at": snap["retrieved_at"],
        "formal_live_validated": False,
        "reason": "Research/source probe only; quote freshness/session executability not verified.",
        "raw_full_universe_persisted": False,
        "low_recovery_seed_count": low["count"],
        "abnormal_drop_seed_count": drop["count"],
        "low_history_probe_verified": low_hist["verified"],
        "drop_history_probe_verified": drop_hist["verified"],
        "not_a_recommendation": True,
    })
    store.write("low-recovery-seed.json", compact_seed(low))
    store.write("abnormal-drop-seed.json", compact_seed(drop))
    store.write("low-recovery-history-probe.json", {
        k: v for k, v in low_hist.items() if k not in {"research_pack", "watchlist"}
    })
    store.write("abnormal-drop-history-probe.json", {
        k: v for k, v in drop_hist.items() if k not in {"research_pack", "watchlist"}
    })
    if low_hist.get("research_pack") is not None:
        store.write("D-low-recovery-research-pack.json", low_hist["research_pack"])
    if drop_hist.get("research_pack") is not None:
        store.write("F-abnormal-drop-research-pack.json", drop_hist["research_pack"])
    if drop_hist.get("watchlist") is not None:
        store.write("F-watchlist-proposal.json", drop_hist["watchlist"])
    print(dumps(read_summary(root)))


def read_summary(root):
    return json.loads((Path(root) / "summary.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
