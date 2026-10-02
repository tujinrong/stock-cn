#!/usr/bin/env python3
"""Run bounded, structural prompt-stability improvements.

No model/API call and no future P&L feedback. PromptLab enforces the cumulative
maximum-ten-round budget and protects the immutable investment-intent block.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stock_cn.variant_prompts import (
    ISSUES, PromptLab, stable_patch, validate_prompt, variant_root,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--variant", required=True)
    p.add_argument("--issues", nargs="+", required=True)
    p.add_argument("--rounds", type=int, default=1)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    unknown = sorted(set(args.issues) - set(ISSUES))
    if unknown:
        raise ValueError("unknown stability issue codes: " + ",".join(unknown))

    root = variant_root(repo, args.variant)
    baseline = (root / "prompt_versions/v000.md").read_text(encoding="utf-8")

    def proposer(current, descriptions):
        candidate = stable_patch(current, descriptions)
        validate_prompt(candidate, baseline)
        return candidate

    def evaluator(candidate):
        validate_prompt(candidate, baseline)
        required = [ISSUES[x] for x in args.issues]
        missing = [x for x in required if x not in candidate]
        return {
            "purpose": "STABILITY",
            "passed": not missing,
            "level": "STRUCTURAL_CONTRACT",
            "missing_required_clauses": missing,
            "future_prices_used": False,
            "performance_feedback_used": False,
            "formal_prompt_modified": False,
        }

    result = PromptLab(repo, args.variant).run(
        proposer, evaluator, args.issues, max_rounds=args.rounds
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
