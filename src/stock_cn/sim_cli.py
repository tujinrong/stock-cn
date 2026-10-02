"""CLI for isolated AI simulation. Run: python -m stock_cn.sim_cli --help."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path

from .sim_agents import Budget, FileAgent, OpenAIResponsesAgent, ScriptedSmokeAgent
from .sim_data import SYMBOLS, fetch_daily, fixture, load_dataset
from .simulation import Simulation, Store, ValidationError, digest, dumps, identifier, read_json, require
from .sim_variants import VariantSimulation as Simulation
from .evaluation import prepare_batch, save_locked_decision, score_locked_decision, summarize


def formal_fingerprints(repo):
    return {str(p.relative_to(repo)): digest(p.read_text(encoding="utf-8"))
            for pat in ("strategies/*/variants/*/holdings.json", "strategies/*/variants/*/holdings.md", "strategies/*/variants/*/init.json", "strategies/*/holdings.json", "strategies/*/holdings.md", "strategies/*/init.json", "strategies/*/ai_input_template.md", "strategies/index.json")
            for p in repo.glob(pat)}


def run_batch(repo, variants, test_id, data, *, agent_factory=None, workers=2, max_calls=100, repair_demo=False):
    repo = Path(repo).resolve()
    identifier(test_id)
    require(1 <= workers <= 4 and len(variants) == len(set(variants)) <= 20, "invalid bounded batch")
    before = formal_fingerprints(repo)
    budget = Budget(max_calls=max_calls)
    outputs = []
    def run_one(variant):
        sim = Simulation(repo, variant[0], variant, test_id, data)
        agent = agent_factory(variant, budget) if agent_factory else ScriptedSmokeAgent(budget, demonstrate_repair=True)
        try:
            sim.initialize()
            for day in data["sessions"][1:]:
                sim.run_day(day, agent)
            report = sim.report()
            if repair_demo:
                sim.store.write("holdings.md", "TEST_ONLY: deliberately damaged derived view\n")
                detection = sim.store.audit()
                repaired = sim.store.audit(repair=True)
                require(detection["ok"] is False and repaired["ok"], "recovery test failed")
                sim.store.write("recovery_test.json", {"before": detection, "after": repaired})
            require(sim.store.audit()["ok"], "ledger validation failed")
            return {"variant": variant, "status": "COMPLETED", "report": report}
        except Exception as exc:
            sim.store.write("failure.json", {"type": type(exc).__name__, "error": str(exc)[:2000]})
            return {"variant": variant, "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, variant): variant for variant in variants}
        for job in concurrent.futures.as_completed(futures):
            try:
                outputs.append(job.result())
            except Exception as exc:
                outputs.append({"variant": futures[job], "status": "FAILED", "error": str(exc)})
    after = formal_fingerprints(repo)
    require(before == after, "FORMAL FILES CHANGED: validation failure")
    result = {"test_id": test_id, "mode": "SIMULATION", "data_kind": data["kind"],
              "agent": "SCRIPTED_SMOKE_NOT_AI" if agent_factory is None else "EXPLICIT_AGENT",
              "formal_files_unchanged": True, "workers": workers, "calls_used": budget.calls,
              "max_calls": budget.maximum, "results": sorted(outputs, key=lambda x: x["variant"]),
              "ok": all(x["status"] == "COMPLETED" for x in outputs),
              "automatic_improvement": "Bounded AI-output validation retries; rebuild damaged derived views from checked events only.",
              "not_investment_performance": True}
    store = Store(repo / "runs/simulations" / test_id)
    store.write("summary.json", result)
    rows = ["|变体|状态|完成天数|成交数|", "|---|---|---:|---:|"]
    for item in result["results"]:
        report = item.get("report", {})
        rows.append(f"|{item['variant']}|{item['status']}|{report.get('completed_days', '—')}|{report.get('fills', '—')}|")
    store.write("summary.md", "# 模拟工程验证\n\n不是投资收益证明。正式持仓未改变。\n\n" + "\n".join(rows) + "\n")
    store.write("improvement.md", "# 自动验证与改善边界\n\n"
                "允许：向AI反馈格式/版本校验错误，在同一决策内有限重试；用完整事件重建损坏的持仓表和每日文件。\n\n"
                "禁止：篡改原始事件、修改买卖方向来绕过拒绝、突破每日次数、为了收益自动放宽风险、覆盖正式策略。\n\n"
                "下一轮研究应补齐历史财务/新闻、真实时点交易限制和权益事件，再作独立前向验证。\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="stock-cn: simulation only; no live brokerage")
    parser.add_argument("--repo", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("selfcheck", help="isolated synthetic engineering validation, no paid AI")
    check.add_argument("--test-id", required=True)
    check.add_argument("--variants", nargs="+", default=["A01", "A02", "A03", "C02", "D02", "E01", "F01"])
    check.add_argument("--workers", type=int, default=2)
    check.add_argument("--max-calls", type=int, default=100)
    probe = sub.add_parser("probe", help="bounded real daily source probe; raw input stays outside repository")
    probe.add_argument("--start", default="2025-08-01")
    probe.add_argument("--end", default="2025-08-08")
    probe.add_argument("--test-id", required=True)
    probe.add_argument("--output", required=True)
    for name in ("prepare", "apply", "replay"):
        p = sub.add_parser(name)
        p.add_argument("--test-id", required=True)
        p.add_argument("--variant", required=True)
        p.add_argument("--data", required=True)
        if name in {"prepare", "apply"}:
            p.add_argument("--day", required=True)
        if name == "apply":
            p.add_argument("--decision", required=True)
        if name == "replay":
            p.add_argument("--agent", choices=["files", "openai", "scripted-smoke"], default="files")
            p.add_argument("--answers")
            p.add_argument("--allow-paid", action="store_true")
            p.add_argument("--model")
            p.add_argument("--max-calls", type=int, default=10)
    travel = sub.add_parser("time-travel", help="prepare the same full variant prompt at a historical date")
    travel.add_argument("--test-id", required=True)
    travel.add_argument("--variant", required=True)
    travel.add_argument("--data", required=True)
    travel.add_argument("--date", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--test-id", required=True)
    audit.add_argument("--variant", required=True)
    audit.add_argument("--repair", action="store_true")
    ep = sub.add_parser("eval-prepare", help="prepare historical AI tasks with future outcomes sealed")
    ep.add_argument("--eval-id", required=True)
    ep.add_argument("--variants", nargs="+", required=True)
    ep.add_argument("--dates", nargs="+", required=True)
    ep.add_argument("--data", required=True)
    el = sub.add_parser("eval-lock", help="lock an AI decision before any outcome scoring")
    el.add_argument("--eval-id", required=True)
    el.add_argument("--variant", required=True)
    el.add_argument("--date", required=True)
    el.add_argument("--decision", required=True)
    es = sub.add_parser("eval-score", help="score a locked decision against future prices and HOLD")
    es.add_argument("--eval-id", required=True)
    es.add_argument("--variant", required=True)
    es.add_argument("--date", required=True)
    es.add_argument("--data", required=True)
    es.add_argument("--horizons", nargs="+", type=int, default=[5, 20, 40])
    esm = sub.add_parser("eval-summary", help="summarize already-scored historical AI decisions")
    esm.add_argument("--eval-id", required=True)
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        if args.command == "selfcheck":
            result = run_batch(repo, args.variants, args.test_id, fixture(), workers=args.workers,
                               max_calls=args.max_calls, repair_demo=True)
        elif args.command == "probe":
            identifier(args.test_id)
            require(not Path(args.output).resolve().is_relative_to(repo), "raw market data output must be outside repository")
            data, attempts = fetch_daily(list(SYMBOLS), args.start, args.end)
            result = {"verified": data is not None, "requested_start": args.start, "requested_end": args.end,
                      "attempts": attempts, "scope": "HTTP/raw daily rows only; not live-feed, news or financial verification"}
            Store(repo / "runs/simulations" / args.test_id).write("source-probe.json", result)
            if data is not None:
                Path(args.output).write_text(dumps(data), encoding="utf-8")
        elif args.command == "eval-prepare":
            data = load_dataset(args.data)
            result = prepare_batch(repo, args.eval_id, args.variants, data, args.dates)
        elif args.command == "eval-lock":
            result = save_locked_decision(
                repo, args.eval_id, args.variant, args.date, read_json(args.decision))
        elif args.command == "eval-score":
            data = load_dataset(args.data)
            result = score_locked_decision(
                repo, args.eval_id, args.variant, args.date, data, tuple(args.horizons))
        elif args.command == "eval-summary":
            result = summarize(repo, args.eval_id)
        elif args.command == "time-travel":
            data = load_dataset(args.data)
            require(args.date in data["sessions"], "time-travel date must be a supplied market session")
            pos = data["sessions"].index(args.date)
            require(pos + 1 < len(data["sessions"]), "time-travel date needs a following session for daily execution")
            execution_day = data["sessions"][pos + 1]
            sim = Simulation(repo, args.variant[0], args.variant, args.test_id, data)
            sim.jump_initialize(args.date)
            request = sim.prepare(execution_day)
            result = {
                "completed": request.get("completed", False),
                "variant": args.variant,
                "target_date": args.date,
                "planned_execution_date": execution_day,
                "ai_input": str(sim.store.root / "requests" / execution_day / "ai_input.md"),
                "time_travel_context": str(sim.store.root / "requests" / execution_day / "time_travel.json"),
                "note": "Same complete variant prompt plus runtime time-travel appendix; target-date close knowledge, next-session open execution.",
            }
        elif args.command == "audit":
            variant, test_id = identifier(args.variant), identifier(args.test_id)
            root = repo / "strategies" / variant[0] / "variants" / variant / "simulations" / test_id
            require(root.resolve().is_relative_to(repo / "strategies" / variant[0] / "variants" / variant), "path escape")
            result = Store(root).audit(repair=args.repair)
        else:
            data = load_dataset(args.data)
            sim = Simulation(repo, args.variant[0], args.variant, args.test_id, data)
            if args.command == "prepare":
                request = sim.prepare(args.day)
                result = {"completed": request.get("completed", False),
                          "ai_input": str(sim.store.root / "requests" / args.day / "ai_input.md")}
            elif args.command == "apply":
                result = sim.apply(args.day, read_json(args.decision))
                sim.report()
            else:
                budget = Budget(max_calls=args.max_calls)
                if args.agent == "openai":
                    agent = OpenAIResponsesAgent(args.model, allow_paid=args.allow_paid, budget=budget)
                elif args.agent == "files":
                    require(bool(args.answers), "--answers directory required")
                    agent = FileAgent(args.answers, budget)
                else:
                    agent = ScriptedSmokeAgent(budget)
                sim.initialize()
                for day in data["sessions"][1:]:
                    sim.run_day(day, agent)
                result = sim.report()
                result["agent"] = args.agent
                sim.store.write("agent.json", {"name": args.agent, "calls": budget.calls})
        print(dumps(result))
        return 0 if result.get("ok", result.get("verified", True)) else 1
    except Exception as exc:
        print(dumps({"status": "FAILED", "type": type(exc).__name__, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
