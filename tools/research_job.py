#!/usr/bin/env python3
"""Prepare and ingest file-based AI research jobs without a model API."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stock_cn.research_jobs import ingest_research_answer, prepare_research_job


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    sub = p.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare")
    prep.add_argument("--spec", required=True, help="JSON spec containing job identity and evidence paths")

    ingest = sub.add_parser("ingest")
    ingest.add_argument("--job-id", required=True)
    ingest.add_argument("--answer", required=True)

    args = p.parse_args()
    repo = Path(args.repo).resolve()

    if args.command == "prepare":
        spec = load(args.spec)
        official = load(repo / spec["official_disclosure_pack_path"])
        candidate = load(repo / spec["candidate_research_pack_path"]) if spec.get("candidate_research_pack_path") else None
        scope = load(repo / spec["universe_scope_path"]) if spec.get("universe_scope_path") else None
        result = prepare_research_job(
            repo,
            job_id=spec["job_id"],
            variant_id=spec["variant_id"],
            decision_date=spec["decision_date"],
            information_cutoff=spec["information_cutoff"],
            mode=spec["mode"],
            symbols=spec["symbols"],
            official_disclosure_pack=official,
            candidate_research_pack=candidate,
            universe_scope=scope,
        )
    else:
        result = ingest_research_answer(repo, args.job_id, load(args.answer))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
