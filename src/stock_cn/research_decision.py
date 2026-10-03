"""Research-only historical decision preparation and locking.

This layer is used when the information cutoff exists but the next real execution
session/price is not available yet. It uses the same full variant prompt and the
same decision JSON contract as simulation/formal Paper Trading, but it never fills
an order or mutates FORMAL state.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .paper_core import validate_decision_contract
from .research_bundle import build_decision_research_bundle, buy_research_preflight
from .research_inputs import load_research_inputs
from .sim_data import number, validate_dataset
from .simulation import Store, digest, holding_table, money, read_json, require
from .time_travel import append_time_travel_prompt, build_time_travel_context
from .variant_prompts import variant_root, validate_prompt


def _source_commit(repo):
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, timeout=3, text=True,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "UNCOMMITTED_LOCAL_WORKSPACE"


def _selected_simulation_prompt(repo, variant):
    root = variant_root(repo, variant)
    pointer_path = root / "simulation_prompt.json"
    if pointer_path.exists():
        pointer = read_json(pointer_path)
        chosen = (root / pointer["path"]).resolve()
        require(chosen.is_relative_to(root.resolve()), "prompt pointer escapes variant")
        text = chosen.read_text(encoding="utf-8")
        require(digest(text) == pointer["sha256"], "simulation prompt hash mismatch")
    else:
        pointer = {
            "version": "v000", "path": "prompt.md",
            "sha256": digest((root / "prompt.md").read_text(encoding="utf-8")),
        }
        text = (root / "prompt.md").read_text(encoding="utf-8")
    baseline = (root / "prompt_versions/v000.md").read_text(encoding="utf-8")
    validate_prompt(text, baseline)
    return root, text, pointer


def _account_at_target(repo, variant, data, target_date):
    root = variant_root(repo, variant)
    init = read_json(root / "init.json")
    cash = number(init["initial_capital_cny"])
    positions = []
    if init["opening_method"] == "ASSUMED_EXISTING_PORTFOLIO":
        total_weight = number(init["cash_weight"]) + sum(
            number(x["weight"]) for x in init["stocks"]
        )
        require(total_weight == 1, "initial weights do not sum to one")
        for stock in init["stocks"]:
            symbol = stock["symbol"]
            require(symbol in data["instruments"], "opening holding missing instrument")
            require(symbol in data["bars"].get(target_date, {}),
                    "opening holding missing target-date price")
            price = number(data["bars"][target_date][symbol]["close"])
            quantity = int(
                number(init["initial_capital_cny"]) * number(stock["weight"])
                / price / 100
            ) * 100
            cash -= quantity * price
            if quantity:
                positions.append({
                    "symbol": symbol,
                    "name": data["instruments"][symbol]["name"],
                    "quantity": quantity,
                    "sellable_quantity": quantity,
                    "average_cost_cny": money(price),
                    "cost_basis_cny": money(quantity * price),
                    "valuation_price_cny": money(price),
                })
    else:
        require(
            not init.get("stocks") or
            all(number(x.get("weight", 0)) == 0 for x in init["stocks"]),
            "cash opening contains positive stock weights",
        )
    value = cash + sum(
        p["quantity"] * number(p["valuation_price_cny"]) for p in positions
    )
    return {
        "strategy_id": variant[0],
        "variant_id": variant,
        "status": "RESEARCH_ONLY",
        "date": target_date,
        "initial_capital_cny": money(init["initial_capital_cny"]),
        "cash_cny": money(cash),
        "total_equity_cny": money(value),
        "positions": positions,
        "_meta": {
            "schema_version": "0.4",
            "mode": "SIMULATION",
            "paper_only": True,
            "variant_id": variant,
            "revision": 0,
            "valuation_time": f"{target_date}T15:00:00+08:00",
            "fees_cny": "0.00",
            "research_only": True,
            "execution_enabled": False,
        },
    }


def _known_symbols(data, cutoff):
    when = datetime.fromisoformat(cutoff)
    return {
        s: m for s, m in data["instruments"].items()
        if not m.get("known_at") or datetime.fromisoformat(m["known_at"]) <= when
    }


def prepare_research_only_request(repo, variant, test_id, data, target_date):
    """Prepare one causal AI decision request with no execution session."""
    repo = Path(repo).resolve()
    validate_dataset(data)
    require(target_date in data["sessions"], "target date is not in supplied history")
    cutoff = f"{target_date}T15:00:00+08:00"
    root, full_prompt, pointer = _selected_simulation_prompt(repo, variant)
    account = _account_at_target(repo, variant, data, target_date)
    held = {p["symbol"] for p in account["positions"]}
    known = _known_symbols(data, cutoff)

    file_research = None
    manifest = repo / "research-inputs" / variant / target_date / "manifest.json"
    if manifest.exists():
        file_research = load_research_inputs(
            repo, variant, target_date, as_of=cutoff
        )
        require(file_research["mode"] == "SIMULATION",
                "research-only historical request requires SIMULATION research inputs")

    scope = (
        file_research.get("universe_scope") if file_research else None
    ) or data.get("universe_scope")
    candidate_pack = (
        file_research.get("candidate_research_pack") if file_research else None
    ) or data.get("candidate_research_pack")

    authorized = set((scope or {}).get("authorized_symbols") or [])
    required = authorized | held
    if required:
        require(required <= set(known),
                "research scope references symbol missing from supplied history")
        known = {s: m for s, m in known.items() if s in required}

    travel = build_time_travel_context(
        data, target_date, target_date,
        symbols=sorted(known), ignore_news=True, execution_date=None,
    )

    official = file_research.get("official_disclosure_pack") if file_research else None
    financials = file_research.get("financial_reviews") if file_research else None
    news = file_research.get("news_research") if file_research else None
    research_input_manifest = None
    if file_research:
        research_input_manifest = {
            "variant_id": file_research["variant_id"],
            "path": file_research["path"],
            "information_cutoff": file_research["information_cutoff"],
            "file_sha256": file_research["file_sha256"],
            "missing_files": file_research["missing_files"],
        }

    decision_research_bundle = None
    if any(x is not None for x in (
        official, financials, news, candidate_pack, research_input_manifest
    )):
        decision_research_bundle = build_decision_research_bundle(
            sorted(known),
            as_of=cutoff,
            official_disclosure_pack=official,
            candidate_research_pack=candidate_pack,
            research_state=None,
            financial_reviews=financials,
            news_research=news,
            market_context={
                "mode": "SIMULATION",
                "submode": "RESEARCH_ONLY_TIME_TRAVEL",
                "fidelity": data.get("fidelity"),
                "execution_available": False,
            },
        )

    source_commit = _source_commit(repo)
    visible_bars = {
        day: {s: b for s, b in rows.items() if s in known}
        for day, rows in data["bars"].items() if day <= target_date
    }
    input_fingerprint = digest({
        "variant": variant,
        "prompt_sha256": digest(full_prompt),
        "target_date": target_date,
        "account": account,
        "known_symbols": sorted(known),
        "visible_bars": visible_bars,
        "research_input_manifest": research_input_manifest,
        "fees": read_json(repo / "config/default.json")
                if (repo / "config/default.json").exists() else {},
    })
    context = {
        "mode": "SIMULATION",
        "submode": "RESEARCH_ONLY_TIME_TRAVEL",
        "strategy_id": variant[0],
        "variant_id": variant,
        "run_id": f"research-{test_id}-{variant}",
        "decision_id": f"research-{test_id}-{variant}-{target_date}",
        "date": target_date,
        "decision_time": cutoff,
        "information_cutoff": cutoff,
        "execution_time": None,
        "timezone": "Asia/Shanghai",
        "execution_basis": "NO_EXECUTION_UNTIL_REAL_NEXT_SESSION_DATA",
        "input_revision": 0,
        "input_commit": source_commit,
        "input_snapshot_sha256": input_fingerprint,
        "account_path": None,
        "authorization": (
            "Research-only historical Paper decision. Lock BUY/SELL/HOLD if justified; "
            "do not claim an execution or fill."
        ),
        "evaluation_start": None,
        "evaluation_end": None,
        "settlement_note": "No execution occurs in this phase.",
        "data_kind": data["kind"],
        "fidelity": data["fidelity"],
    }

    market = {
        s: [{
            "date": d,
            "close": visible_bars[d][s]["close"],
            "source": visible_bars[d][s]["source"],
        } for d in sorted(visible_bars)[-10:] if s in visible_bars[d]]
        for s in known
    }
    authorized_universe = scope if scope is not None else sorted(known)
    tools = {
        "historical_closes": market,
        "candidate_research_pack": candidate_pack,
        "universe_scope": scope,
        "official_disclosure_pack": official,
        "financial_reviews": financials,
        "news_research": news,
        "decision_research_bundle": decision_research_bundle,
        "research_input_manifest": research_input_manifest,
        "tools": (
            "Use only supplied point-in-time material. This phase has no future "
            "execution quote and cannot claim a fill."
        ),
        "limitations": data.get("limitations", []),
    }

    prompt = append_time_travel_prompt(full_prompt, travel)
    fields = {
        "RUN_CONTEXT": json.dumps(context, ensure_ascii=False, indent=2),
        "HOLDINGS_JSON": json.dumps(account, ensure_ascii=False, indent=2),
        "HOLDINGS_TABLE_ROWS": holding_table(account),
        "PREVIOUS_DECISION_SUMMARY": "研究时光穿越起点；尚无此前本测试决策。",
        "AUTHORIZED_UNIVERSE": json.dumps(
            authorized_universe, ensure_ascii=False, indent=2
        ),
        "EVIDENCE_AND_TOOL_CONTEXT": json.dumps(
            tools, ensure_ascii=False, indent=2
        ),
    }
    for name, value in fields.items():
        prompt = prompt.replace("{{" + name + "}}", value)
    require(not re.search(r"\{\{[^}]+\}\}", prompt),
            "unresolved research-only prompt variable")

    out_root = repo / "runs" / "research-decisions" / test_id / variant / target_date
    store = Store(out_root)
    request = {
        "context": context,
        "holdings": account,
        "market": market,
        "prompt": prompt,
        "prompt_sha256": digest(prompt),
        "source_holdings": account,
        "decision_research_bundle": decision_research_bundle,
        "research_input_manifest": research_input_manifest,
        "candidate_research_pack": candidate_pack,
        "universe_scope": scope,
        "prompt_pointer": pointer,
        "execution_status": "WAITING_FOR_REAL_NEXT_SESSION_DATA",
    }
    store.write("request.json", request)
    store.write("ai_input.md", prompt)
    store.write("time_travel.json", travel)
    store.write("account_at_target.json", account)
    if research_input_manifest is not None:
        store.write("research_input_manifest.json", research_input_manifest)
    return request


def validate_research_only_decision(repo, variant, response, request):
    repo = Path(repo).resolve()
    known = set(request["market"])
    held = {p["symbol"] for p in request["holdings"]["positions"]}
    scope = request.get("universe_scope") or {}
    buy_candidates = set(scope.get("authorized_symbols") or known)

    def symbol_validator(symbol):
        require(symbol in known or symbol in held,
                "research-only symbol outside visible candidates/holdings")
        require(not symbol.startswith(("688", "689", "300", "301")),
                "excluded board")

    def quote_validator(order, req):
        if order["side"] == "BUY":
            require(order["symbol"] in buy_candidates,
                    "research-only BUY outside authorized candidate set")
            if req.get("decision_research_bundle") is not None:
                preflight = buy_research_preflight(
                    req["decision_research_bundle"], order["symbol"]
                )
                require(preflight["ready"],
                        "BUY research preflight failed: " + ",".join(preflight["reasons"]))
        elif order["side"] == "SELL":
            require(order["symbol"] in held,
                    "research-only SELL is not a current holding")
        rows = req["market"].get(order["symbol"], [])
        require(bool(rows), "no visible target-date quote")
        last = rows[-1]
        require(number(order["reference_price_cny"]) == number(last["close"]),
                "reference price does not match target-date close")
        require(order["quote_time"] == req["context"]["information_cutoff"],
                "reference quote must use target-date cutoff")
        require(order["quote_source"] == last["source"],
                "reference quote source mismatch")

    validate_decision_contract(
        response, request, symbol_validator, quote_validator=quote_validator
    )
    return True


def lock_research_only_decision(repo, variant, test_id, target_date, decision):
    repo = Path(repo).resolve()
    root = repo / "runs" / "research-decisions" / test_id / variant / target_date
    request_path = root / "request.json"
    require(request_path.exists(), "research-only request missing")
    request = read_json(request_path)
    validate_research_only_decision(repo, variant, decision, request)
    store = Store(root)
    lock = {
        "variant_id": variant,
        "target_date": target_date,
        "prompt_sha256": request["prompt_sha256"],
        "decision_sha256": digest(decision),
        "execution_status": "WAITING_FOR_REAL_NEXT_SESSION_DATA",
        "future_execution_data_seen": False,
        "formal_state_changed": False,
    }
    decision_path = root / "decision.json"
    if decision_path.exists():
        require(read_json(decision_path) == decision,
                "research-only decision already locked with different content")
        require(read_json(root / "decision.lock.json") == lock,
                "research-only decision lock changed")
        return lock
    store.write("decision.json", decision)
    store.write("decision.lock.json", lock)
    return lock
