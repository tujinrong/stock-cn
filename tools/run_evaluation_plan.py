#!/usr/bin/env python3
"""Prepare or score a declared historical AI evaluation plan.

Raw market data stays in a temporary file/runtime. Git stores only causal AI inputs,
locked decisions, execution records and post-lock scores.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from stock_cn.evaluation import prepare_batch, save_locked_decision, score_locked_decision, summarize
from stock_cn.sim_data import SYMBOLS, fetch_daily
from stock_cn.universe import fetch_candidate_history
from stock_cn.simulation import Store, digest, dumps, require


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def plan_path(repo, eval_id):
    matches = list((Path(repo) / "evaluation-plans").glob("*.json"))
    for p in matches:
        obj = load(p)
        if obj.get("eval_id") == eval_id:
            return p, obj
    raise ValueError("evaluation plan not found")


def fetch(plan):
    symbols = plan.get("symbols") or list(SYMBOLS)
    if set(symbols) <= set(SYMBOLS):
        data, attempts = fetch_daily(
            symbols, plan["history_start"], plan["history_end"]
        )
    else:
        universe = plan.get("universe")
        require(isinstance(universe, list) and universe,
                "non-default evaluation symbols require an explicit bounded universe")
        by_symbol = {x["symbol"]: x for x in universe}
        require(set(symbols) == set(by_symbol),
                "evaluation symbols/universe mismatch")
        require(len(symbols) <= 30,
                "historical AI evaluation universe exceeds bounded budget")
        seed = {
            "kind": "BOUNDED_CANDIDATE_SEED",
            "purpose": "DECLARED_HISTORICAL_EVALUATION_UNIVERSE",
            "count": len(symbols),
            "rows": [{
                "symbol": s,
                "name": by_symbol[s]["name"],
                "risk_tags": list(by_symbol[s].get("risk_tags", [])),
            } for s in symbols],
            "source": "evaluation plan declared universe",
            "survivorship_warning": plan.get(
                "universe_warning",
                "Declared bounded historical evaluation universe; not full-market coverage."
            ),
        }
        data, attempts = fetch_candidate_history(
            seed,
            plan["history_start"],
            plan["history_end"],
            max_symbols=len(symbols),
        )
    if data is None:
        raise RuntimeError(
            "historical source failed: " + json.dumps(attempts, ensure_ascii=False)
        )
    return data, attempts


def prepare(repo, plan):
    data, attempts = fetch(plan)
    result = prepare_batch(repo, plan["eval_id"], plan["variants"], data, plan["target_dates"],
                           prompt_selections=plan.get('prompt_selections'))
    store = Store(Path(repo) / "runs" / "evaluations" / plan["eval_id"])
    store.write("source-probe.json", {
        "phase": "PREPARE", "attempts": attempts,
        "history_start": plan["history_start"], "history_end": plan["history_end"],
        "raw_market_data_persisted": False,
    })
    return result


def score(repo, plan):
    answer_root = Path(repo) / "evaluation-answers" / plan["eval_id"]
    pending = []
    points = []
    # Check the complete declared batch before mutating locks or acquiring outcomes.
    # A subset of available answers must never be reported as a completed plan.
    for variant in plan["variants"]:
        for target in plan["target_dates"]:
            answer = answer_root / variant / f"{target}.json"
            decision = (Path(repo) / 'runs/evaluations' / plan['eval_id'] /
                        'decisions' / variant / f'{target}.json')
            lock = decision.with_suffix('.lock.json')
            require(decision.exists() == lock.exists(),
                    f'incomplete decision lock: {variant} {target}')
            if lock.exists():
                sealed = load(lock)
                saved = load(decision)
                require(sealed.get('locked') is True and
                        sealed.get('future_outcomes_seen_by_decision_phase') is False and
                        sealed.get('decision_sha256') == digest(saved),
                        f'invalid decision lock: {variant} {target}')
                if answer.exists():
                    require(digest(load(answer)) == digest(saved),
                            f'answer differs from locked decision: {variant} {target}')
            else:
                require(answer.is_file(), f'planned answer missing: {variant} {target}')
                pending.append((variant, target, load(answer)))
            points.append((variant, target))
    require(points, 'evaluation plan has no decision points')
    for variant, target, answer in pending:
        save_locked_decision(repo, plan['eval_id'], variant, target, answer)
    # Only after every decision is immutable may this phase acquire future prices.
    data, attempts = fetch(plan)
    results = []
    for variant, target in points:
        results.append(score_locked_decision(
            repo, plan["eval_id"], variant, target, data,
            tuple(plan.get("score_horizons", [5, 20, 40])),
        ))
    require(results, "no answers found to score")
    summary = summarize(repo, plan["eval_id"])
    Store(Path(repo) / "runs" / "evaluations" / plan["eval_id"]).write("score-source-probe.json", {
        "phase": "SCORE_AFTER_LOCK", "attempts": attempts,
        "raw_market_data_persisted": False,
        "future_outcomes_not_used_for_prompt_improvement": True,
    })
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--eval-id", required=True)
    p.add_argument("--phase", choices=["prepare", "score"], required=True)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    _, plan = plan_path(repo, args.eval_id)
    result = prepare(repo, plan) if args.phase == "prepare" else score(repo, plan)
    print(dumps(result))


if __name__ == "__main__":
    main()
