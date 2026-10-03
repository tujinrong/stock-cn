#!/usr/bin/env python3
"""Validate and lock a research-only AI decision answer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stock_cn.research_decision import lock_research_only_decision


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--answer", required=True)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    wrapper = json.loads((repo / args.answer).read_text(encoding="utf-8"))
    lock = lock_research_only_decision(
        repo,
        wrapper["variant_id"],
        wrapper["test_id"],
        wrapper["target_date"],
        wrapper["decision"],
    )
    print(json.dumps(lock, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
