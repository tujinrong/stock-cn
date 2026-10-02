#!/usr/bin/env python3
"""Prepare bounded AI research jobs from repository evidence/candidate outputs."""
from __future__ import annotations

import argparse
import json
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--request", required=True)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    spec = load(repo / args.request)

    official = load(repo / spec["official_disclosure_pack_path"])
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
