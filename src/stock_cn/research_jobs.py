"""File-based AI research job preparation and answer ingestion.

GitHub/CI can prepare bounded research jobs without a model API. A ChatGPT/manual
research step may then produce an answer JSON. Ingestion validates causality and
provenance and writes research-input files only; it never changes holdings or trades.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

from .evidence import validate_official_disclosure_pack
from .research_bundle import validate_financial_review, validate_news_research
from .simulation import Store, digest, read_json, require
from .variant_prompts import variant_root


def _aware(value, field):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(field + " must be timezone-aware")
    return dt


def _job_root(repo, job_id):
    repo = Path(repo).resolve()
    if not isinstance(job_id, str) or not job_id or any(x in job_id for x in "/\"):
        raise ValueError("invalid research job id")
    root = repo / "runs" / "research" / "jobs" / job_id
    if not root.resolve().is_relative_to((repo / "runs" / "research" / "jobs").resolve()):
        raise ValueError("research job path escape")
    return root


def prepare_research_job(
    repo,
    *,
    job_id,
    variant_id,
    decision_date,
    information_cutoff,
    mode,
    symbols,
    official_disclosure_pack,
    candidate_research_pack=None,
    universe_scope=None,
):
    """Prepare a causal research task package for an external/ChatGPT AI step."""
    repo = Path(repo).resolve()
    datetime.fromisoformat(decision_date)
    cutoff = _aware(information_cutoff, "information_cutoff")
    if mode not in {"SIMULATION", "FORMAL"}:
        raise ValueError("invalid research job mode")
    if not symbols or len(symbols) > 30 or len(symbols) != len(set(symbols)):
        raise ValueError("research job requires 1..30 unique symbols")
    validate_official_disclosure_pack(
        official_disclosure_pack,
        as_of=information_cutoff,
        required_symbols=symbols,
    )

    candidate_symbols = {
        x.get("symbol") for x in (candidate_research_pack or {}).get("candidates", [])
        if isinstance(x, dict) and x.get("symbol")
    }
    if not candidate_symbols <= set(symbols):
        raise ValueError("candidate pack contains symbol outside research job")
    if universe_scope is not None:
        authorized = set(universe_scope.get("authorized_symbols") or [])
        if candidate_symbols and not candidate_symbols <= authorized:
            raise ValueError("candidate pack escapes universe scope")

    root = _job_root(repo, job_id)
    store = Store(root)
    request = {
        "kind": "AI_RESEARCH_JOB",
        "job_id": job_id,
        "variant_id": variant_id,
        "series_id": variant_id[0],
        "mode": mode,
        "decision_date": decision_date,
        "information_cutoff": information_cutoff,
        "symbols": list(symbols),
        "official_disclosure_pack": official_disclosure_pack,
        "candidate_research_pack": candidate_research_pack,
        "universe_scope": universe_scope,
        "required_outputs": {
            "financial_reviews": (
                "One REVIEWED object per researched symbol, based on actual official report "
                "content; each fact must include a source."
            ),
            "news_research": (
                "SEARCHED/NO_RELEVANT_RECENT_NEWS/UNAVAILABLE/NOT_CHECKED with causal "
                "publication timestamps and material-fact official recheck status."
            ),
        },
        "rules": [
            "Do not use information published after information_cutoff.",
            "Official disclosure metadata is only a reference; read/interpret actual report content before claiming financial facts.",
            "News is a lead source; material company facts should be rechecked against official disclosure where possible.",
            "Return research only. Do not output or execute a trade in this job.",
        ],
        "formal_execution": False,
    }
    request["request_sha256"] = digest({k: v for k, v in request.items() if k != "request_sha256"})

    task = [
        f"# AI研究任务 {job_id}",
        "",
        f"- 变体：{variant_id}",
        f"- 模式：{mode}",
        f"- 决策日期：{decision_date}",
        f"- 信息截止：{information_cutoff}",
        f"- 股票：{', '.join(symbols)}",
        "",
        "本任务只做财务/公告/新闻研究，不做交易。",
        "只能使用信息截止时点以前已经公开的资料。",
        "请阅读官方定期报告的实际内容并生成 financial_reviews；同时完成近期新闻研究。",
        "所有关键事实必须保留来源，资料不足必须写 data_gaps。",
        "",
        "输出JSON顶层必须包含：financial_reviews、news_research。",
    ]
    store.write("request.json", request)
    store.write("ai_task.md", "
".join(task) + "
")
    store.write("official-disclosure-pack.json", official_disclosure_pack)
    if candidate_research_pack is not None:
        store.write("candidate-research-pack.json", candidate_research_pack)
    if universe_scope is not None:
        store.write("universe-scope.json", universe_scope)
    return request


def validate_research_answer(answer, request):
    if not isinstance(answer, dict):
        raise ValueError("research answer must be an object")
    if answer.get("job_id") not in (None, request["job_id"]):
        raise ValueError("research answer belongs to another job")
    if answer.get("variant_id") not in (None, request["variant_id"]):
        raise ValueError("research answer belongs to another variant")
    if answer.get("information_cutoff") not in (None, request["information_cutoff"]):
        raise ValueError("research answer cutoff mismatch")

    financials = answer.get("financial_reviews")
    if not isinstance(financials, dict):
        raise ValueError("research answer financial_reviews missing")
    required = set(request["symbols"])
    if set(financials) != required:
        missing = sorted(required - set(financials))
        extra = sorted(set(financials) - required)
        raise ValueError(
            "financial review symbol coverage mismatch; missing=" + ",".join(missing) +
            " extra=" + ",".join(extra)
        )
    for symbol, review in financials.items():
        validate_financial_review(
            review, symbol=symbol, as_of=request["information_cutoff"]
        )

    news = answer.get("news_research")
    validate_news_research(
        news,
        as_of=request["information_cutoff"],
        allowed_symbols=request["symbols"],
    )
    return True


def ingest_research_answer(repo, job_id, answer):
    """Validate one AI research answer and write a decision-date research-input set."""
    repo = Path(repo).resolve()
    root = _job_root(repo, job_id)
    request_path = root / "request.json"
    if not request_path.exists():
        raise ValueError("research job request missing")
    request = read_json(request_path)
    expected_sha = request.get("request_sha256")
    actual_sha = digest({k: v for k, v in request.items() if k != "request_sha256"})
    require(expected_sha == actual_sha, "research job request changed after preparation")
    validate_research_answer(answer, request)

    answer = copy.deepcopy(answer)
    answer["job_id"] = request["job_id"]
    answer["variant_id"] = request["variant_id"]
    answer["information_cutoff"] = request["information_cutoff"]
    answer["answer_sha256"] = digest({
        k: v for k, v in answer.items() if k != "answer_sha256"
    })

    answer_path = root / "answer.json"
    if answer_path.exists():
        require(read_json(answer_path) == answer,
                "research answer already locked with different content")
    else:
        Store(root).write("answer.json", answer)

    target = (
        repo / "research-inputs" / request["variant_id"] / request["decision_date"]
    )
    target_store = Store(target)
    manifest = {
        "variant_id": request["variant_id"],
        "mode": request["mode"],
        "decision_date": request["decision_date"],
        "information_cutoff": request["information_cutoff"],
        "source_commit": None,
        "formal_execution": False,
        "research_job_id": request["job_id"],
        "research_request_sha256": expected_sha,
        "research_answer_sha256": answer["answer_sha256"],
    }

    documents = {
        "manifest.json": manifest,
        "official-disclosure-pack.json": request["official_disclosure_pack"],
        "financial-reviews.json": answer["financial_reviews"],
        "news-research.json": answer["news_research"],
    }
    if request.get("candidate_research_pack") is not None:
        documents["candidate-research-pack.json"] = request["candidate_research_pack"]
    if request.get("universe_scope") is not None:
        documents["universe-scope.json"] = request["universe_scope"]

    for filename, value in documents.items():
        p = target / filename
        if p.exists():
            require(read_json(p) == value,
                    "research-input file already exists with different content: " + filename)
        else:
            target_store.write(filename, value)
    return {
        "job_id": job_id,
        "variant_id": request["variant_id"],
        "decision_date": request["decision_date"],
        "research_input_path": str(target.relative_to(repo)),
        "answer_sha256": answer["answer_sha256"],
        "holdings_changed": False,
        "trade_executed": False,
    }
