#!/usr/bin/env python3
"""Prepare bounded AI research jobs from repository evidence/candidate outputs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from stock_cn.research_jobs import prepare_research_job


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def filtered_candidate_pack(pack, symbols):
    if pack is None:
        return None
    symbols = set(symbols)
    out = dict(pack)
    out["candidates"] = [
        x for x in pack.get("candidates", [])
        if x.get("symbol") in symbols
    ]
    out["selected_count"] = len(out["candidates"])
    out["candidate_budget"] = min(
        int(pack.get("candidate_budget") or len(out["candidates"]) or 1),
        max(1, len(out["candidates"]))
    )
    if not out["candidates"]:
        raise ValueError("requested research symbols are absent from candidate pack")
    return out


def filtered_official_pack(pack, symbols, cutoff):
    """Filter a later-retrieved official pack back to the decision-time frontier."""
    symbols = set(symbols)
    cutoff_dt = datetime.fromisoformat(cutoff)
    if cutoff_dt.tzinfo is None:
        raise ValueError("information_cutoff must be timezone-aware")
    out = dict(pack)
    results = []
    for result in pack.get("results", []):
        if result.get("symbol") not in symbols:
            continue
        r = dict(result)
        items = []
        for item in result.get("items", []):
            published = datetime.fromisoformat(item["published_at"])
            if published.tzinfo is None:
                raise ValueError("official disclosure timestamp must be timezone-aware")
            if published <= cutoff_dt:
                items.append(item)
        r["items"] = items
        # Provider status describes query success, not whether causal items remain.
        if r.get("provider_status") == "OK" and not items:
            r["provider_status"] = "EMPTY"
        results.append(r)
    if {x.get("symbol") for x in results} != symbols:
        raise ValueError("official disclosure pack does not cover requested research symbols")

    out["results"] = results
    out["symbols_requested"] = list(sorted(symbols))
    out["symbols_ok_or_empty"] = [
        r["symbol"] for r in results if r.get("provider_status") in {"OK", "EMPTY"}
    ]
    out["symbols_failed"] = [
        r["symbol"] for r in results if r.get("provider_status") == "FAILED"
    ]
    out["complete_for_requested_symbols"] = not out["symbols_failed"]
    all_items = [x for r in results for x in r.get("items", [])]
    out["latest_periodic_report_refs"] = sorted(
        [x for x in all_items if x.get("is_periodic_report_body")],
        key=lambda x: x["published_at"], reverse=True
    )[:len(symbols) * 3]
    important_categories = {
        "EARNINGS", "BUYBACK", "HOLDER_CHANGE", "CONTRACT", "MNA",
        "FINANCING", "GOVERNANCE", "RISK", "DIVIDEND",
    }
    out["important_recent_refs"] = sorted(
        [x for x in all_items if x.get("category") in important_categories],
        key=lambda x: x["published_at"], reverse=True
    )[:50]
    out["as_of"] = cutoff
    out["causal_filter_applied"] = True
    out["causal_filter_cutoff"] = cutoff
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--request", required=True)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    spec = load(repo / args.request)

    official = filtered_official_pack(
        load(repo / spec["official_disclosure_pack_path"]),
        spec["symbols"],
        spec["information_cutoff"],
    )
    candidate = None
    if spec.get("candidate_research_pack_path"):
        candidate = filtered_candidate_pack(
            load(repo / spec["candidate_research_pack_path"]),
            spec["symbols"],
        )
    scope = {
        "authorized_symbols": list(spec["symbols"]),
        "coverage": spec.get("coverage", "BOUNDED_RESEARCH_CANDIDATES_ONLY"),
        "not_full_a_share_claim": True,
    }

    result = prepare_research_job(
        repo,
        job_id=spec["job_id"],
        variant_id=spec["variant_id"],
        decision_date=spec["decision_date"],
        information_cutoff=spec["information_cutoff"],
        mode=spec.get("mode", "SIMULATION"),
        symbols=spec["symbols"],
        official_disclosure_pack=official,
        candidate_research_pack=candidate,
        universe_scope=scope,
    )
    print(json.dumps({
        "job_id": result["job_id"],
        "variant_id": result["variant_id"],
        "decision_date": result["decision_date"],
        "symbols": result["symbols"],
        "formal_execution": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
