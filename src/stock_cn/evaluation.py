"""Point-in-time historical AI evaluation.

Phase A prepares causal time-travel prompts with no future outcome data.
Phase B scores a locked decision against future closes and a HOLD counterfactual.
Scoring never modifies prompts, strategy text, prompt-improvement state or FORMAL accounts.
"""
from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

from .simulation import Store, digest, money, read_json, require
from .sim_variants import VariantSimulation
from .time_travel import _latest_structural_break
from .variant_prompts import variant_root


def _safe_id(value):
    from .simulation import identifier
    return identifier(value)


def _entry_id(variant, target_date):
    return f"{variant}-{target_date}"


def _relative(repo, path):
    return str(Path(path).resolve().relative_to(Path(repo).resolve()))


def prepare_point(repo, eval_id, variant, data, target_date):
    """Prepare one isolated historical AI request without future outcomes."""
    repo = Path(repo).resolve()
    eval_id = _safe_id(eval_id)
    variant = _safe_id(variant)
    require(target_date in data["sessions"], "evaluation target must be a supplied session")
    pos = data["sessions"].index(target_date)
    require(pos + 1 < len(data["sessions"]), "target needs a following execution session")
    execution_date = data["sessions"][pos + 1]
    test_id = f"eval-{eval_id}-{target_date.replace('-', '')}"
    sim = VariantSimulation(repo, variant[0], variant, test_id, data)
    sim.jump_initialize(target_date)
    request = sim.prepare(execution_date)
    require(not request.get("completed"), "fresh evaluation request unexpectedly completed")
    root = repo / "runs" / "evaluations" / eval_id
    store = Store(root)
    entry = {
        "entry_id": _entry_id(variant, target_date),
        "eval_id": eval_id,
        "variant": variant,
        "target_date": target_date,
        "execution_date": execution_date,
        "prompt_sha256": request["prompt_sha256"],
        "input_revision": request["context"]["input_revision"],
        "input_commit": request["context"]["input_commit"],
        "simulation_test_id": test_id,
        "request_path": _relative(repo, sim.store.path(f"requests/{execution_date}/request.json")),
        "ai_input_path": _relative(repo, sim.store.path(f"requests/{execution_date}/ai_input.md")),
        "time_travel_path": _relative(repo, sim.store.path(f"requests/{execution_date}/time_travel.json")),
        "decision_path": f"runs/evaluations/{eval_id}/decisions/{variant}/{target_date}.json",
        "score_path": f"runs/evaluations/{eval_id}/scores/{variant}/{target_date}.json",
        "status": "WAITING_FOR_AI",
        "future_outcomes_in_prompt": False,
    }
    store.write(f"entries/{variant}/{target_date}.json", entry)
    return entry


def prepare_batch(repo, eval_id, variants, data, target_dates):
    """Prepare bounded independent requests; never score in this phase."""
    repo = Path(repo).resolve()
    _safe_id(eval_id)
    require(len(variants) == len(set(variants)) and 1 <= len(variants) <= 20,
            "invalid evaluation variants")
    require(len(target_dates) == len(set(target_dates)) and 1 <= len(target_dates) <= 20,
            "invalid evaluation dates")
    before = {
        str(p.relative_to(repo)): digest(p.read_text(encoding="utf-8"))
        for p in repo.glob("strategies/*/variants/*/holdings.json")
    }
    entries = [prepare_point(repo, eval_id, v, data, d) for v in variants for d in target_dates]
    after = {
        str(p.relative_to(repo)): digest(p.read_text(encoding="utf-8"))
        for p in repo.glob("strategies/*/variants/*/holdings.json")
    }
    require(before == after, "formal holdings changed during evaluation preparation")
    store = Store(repo / "runs" / "evaluations" / eval_id)
    manifest = {
        "eval_id": eval_id,
        "mode": "HISTORICAL_AI_EVALUATION",
        "phase": "DECISION_PREPARATION_ONLY",
        "variants": list(variants),
        "target_dates": list(target_dates),
        "entries": entries,
        "future_outcomes_in_prompt": False,
        "decision_source": "EXTERNAL_OR_CHATGPT_FILE",
        "scoring_policy": "Scores are generated only after decisions are locked; never used by PromptLab.",
    }
    store.write("manifest.json", manifest)
    rows = ["|变体|历史时点|执行日|状态|AI输入|", "|---|---|---|---|---|"]
    for e in entries:
        rows.append(f"|{e['variant']}|{e['target_date']}|{e['execution_date']}|WAITING_FOR_AI|{e['ai_input_path']}|")
    store.write("queue.md", "# 历史AI评价任务\n\n未来结果未进入AI输入。\n\n" + "\n".join(rows) + "\n")
    return manifest


def _load_entry(repo, eval_id, variant, target_date):
    p = Path(repo) / "runs" / "evaluations" / eval_id / "entries" / variant / f"{target_date}.json"
    require(p.is_file(), "evaluation entry missing")
    return read_json(p)


def save_locked_decision(repo, eval_id, variant, target_date, decision):
    """Lock a decision only when it matches the prepared historical request exactly."""
    repo = Path(repo).resolve()
    entry = _load_entry(repo, eval_id, variant, target_date)
    request = read_json(repo / entry["request_path"])
    require(request["prompt_sha256"] == entry["prompt_sha256"], "prepared prompt changed")
    # No market data is loaded in the lock phase. Full trading-rule validation is
    # deliberately deferred to score_locked_decision, after the decision is immutable.
    c = request["context"]
    require(isinstance(decision, dict), "decision must be an object")
    for field in ("strategy_id", "variant_id", "mode", "run_id", "decision_id", "date",
                  "decision_time", "input_revision", "input_commit"):
        require(decision.get(field) == c[field], f"decision identity mismatch: {field}")
    require(decision.get("schema_version") == "0.3-draft", "decision schema mismatch")
    require(decision.get("status") in {"READY", "INSUFFICIENT_DATA", "NOT_INITIALIZED",
                                       "NOT_AUTHORIZED", "INVALID_INPUT"},
            "decision status invalid")
    root = repo / "runs" / "evaluations" / eval_id
    p = root / "decisions" / variant / f"{target_date}.json"
    require(not p.exists(), "decision already locked; create a new eval_id to change it")
    Store(root).write(f"decisions/{variant}/{target_date}.json", decision)
    lock = {
        "entry_id": entry["entry_id"],
        "prompt_sha256": entry["prompt_sha256"],
        "decision_sha256": digest(decision),
        "locked": True,
        "future_outcomes_seen_by_decision_phase": False,
    }
    Store(root).write(f"decisions/{variant}/{target_date}.lock.json", lock)
    return lock


def _valuation(state, data, day):
    value = Decimal(str(state["cash_cny"]))
    for p in state["positions"]:
        require(p["symbol"] in data["bars"].get(day, {}), f"missing future valuation bar: {p['symbol']} {day}")
        value += Decimal(str(data["bars"][day][p["symbol"]]["close"])) * p["quantity"]
    return value


def _has_break(data, symbol, start_date, end_date):
    rows = [(d, data["bars"][d][symbol]) for d in data["sessions"]
            if start_date <= d <= end_date and symbol in data["bars"].get(d, {})]
    return _latest_structural_break(rows) if len(rows) >= 2 else None


def score_locked_decision(repo, eval_id, variant, target_date, data, horizons=(5, 20, 40)):
    """Score a locked decision. Future data exists only here, after the lock."""
    repo = Path(repo).resolve()
    entry = _load_entry(repo, eval_id, variant, target_date)
    decision_path = repo / entry["decision_path"]
    lock_path = decision_path.with_suffix(".lock.json")
    require(decision_path.is_file() and lock_path.is_file(), "locked decision missing")
    decision = read_json(decision_path)
    lock = read_json(lock_path)
    require(lock["decision_sha256"] == digest(decision), "locked decision changed")
    request = read_json(repo / entry["request_path"])
    require(request["prompt_sha256"] == lock["prompt_sha256"], "prompt changed after decision lock")
    sim = VariantSimulation(repo, variant[0], variant, entry["simulation_test_id"], data)
    sim.validate_decision(decision, request)
    execution = sim.apply(entry["execution_date"], decision)
    actual = sim.store.load()
    baseline = copy.deepcopy(request["holdings"])
    sessions = data["sessions"]
    ex_i = sessions.index(entry["execution_date"])
    scores = []
    held_symbols = sorted({p["symbol"] for p in actual["positions"]} |
                          {p["symbol"] for p in baseline["positions"]})
    for h in horizons:
        require(type(h) is int and h > 0, "horizon must be a positive integer")
        idx = ex_i + h
        if idx >= len(sessions):
            scores.append({"horizon_sessions": h, "status": "INSUFFICIENT_FUTURE_SESSIONS"})
            continue
        day = sessions[idx]
        breaks = {s: _has_break(data, s, entry["execution_date"], day) for s in held_symbols}
        breaks = {s: b for s, b in breaks.items() if b}
        if breaks:
            scores.append({"horizon_sessions": h, "date": day,
                           "status": "UNSCORABLE_PRICE_BASIS_BREAK", "breaks": breaks})
            continue
        actual_equity = _valuation(actual, data, day)
        hold_equity = _valuation(baseline, data, day)
        start_equity = Decimal(str(request["holdings"]["total_equity_cny"]))
        scores.append({
            "horizon_sessions": h,
            "date": day,
            "status": "SCORED",
            "actual_equity_cny": money(actual_equity),
            "hold_counterfactual_equity_cny": money(hold_equity),
            "actual_return_pct": str((actual_equity / start_equity - 1) * 100),
            "hold_return_pct": str((hold_equity / start_equity - 1) * 100),
            "incremental_pnl_vs_hold_cny": money(actual_equity - hold_equity),
            "incremental_return_vs_hold_pct": str((actual_equity / hold_equity - 1) * 100),
        })
    result = {
        "eval_id": eval_id, "variant": variant, "target_date": target_date,
        "execution_date": entry["execution_date"],
        "prompt_sha256": lock["prompt_sha256"],
        "decision_sha256": lock["decision_sha256"],
        "action": decision.get("action"),
        "execution": execution,
        "scores": scores,
        "future_outcomes_were_separate_from_decision_phase": True,
        "eligible_for_prompt_auto_improvement": False,
        "note": "Outcome scores compare this locked point decision with HOLD; they are not fed to PromptLab.",
    }
    root = repo / "runs" / "evaluations" / eval_id
    Store(root).write(f"scores/{variant}/{target_date}.json", result)
    return result


def summarize(repo, eval_id):
    repo = Path(repo).resolve()
    root = repo / "runs" / "evaluations" / eval_id
    scores = []
    for p in sorted((root / "scores").glob("*/*.json")) if (root / "scores").exists() else []:
        scores.append(read_json(p))
    summary = {"eval_id": eval_id, "scored_entries": len(scores), "entries": scores}
    Store(root).write("summary.json", summary)
    rows = ["|变体|历史时点|动作|5日vs HOLD|20日vs HOLD|40日vs HOLD|", "|---|---|---|---:|---:|---:|"]
    for s in scores:
        m = {x["horizon_sessions"]: x for x in s["scores"]}
        def val(h):
            x = m.get(h, {})
            return x.get("incremental_return_vs_hold_pct", x.get("status", "—"))
        rows.append(f"|{s['variant']}|{s['target_date']}|{s.get('action')}|{val(5)}|{val(20)}|{val(40)}|")
    Store(root).write("summary.md", "# 历史AI点决策评价\n\n评分不回流到提示词自动改进。\n\n" + "\n".join(rows) + "\n")
    return summary
