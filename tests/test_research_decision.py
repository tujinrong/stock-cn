import copy
import json
from pathlib import Path

import pytest

from test_simulation import repo
from stock_cn.research_decision import (
    lock_research_only_decision,
    prepare_research_only_request,
    validate_research_only_decision,
)
from stock_cn.sim_agents import decision_base
from stock_cn.sim_data import fixture
from stock_cn.variant_prompts import materialize
from stock_cn.simulation import ValidationError


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def one_symbol_data(target="2025-08-08"):
    data = fixture()
    keep = {"600036.SH"}
    data["instruments"] = {s: m for s, m in data["instruments"].items() if s in keep}
    data["bars"] = {
        d: {s: b for s, b in rows.items() if s in keep}
        for d, rows in data["bars"].items()
        if d <= target
    }
    data["sessions"] = [d for d in data["sessions"] if d <= target]
    return data


def setup_research(repo, date="2025-08-08", *, include_financial=True):
    root = repo / f"research-inputs/D02/{date}"
    write(root / "manifest.json", {
        "variant_id": "D02",
        "mode": "SIMULATION",
        "decision_date": date,
        "information_cutoff": f"{date}T15:00:00+08:00",
        "source_commit": "TEST",
        "formal_execution": False,
    })
    report = {
        "symbol": "600036.SH",
        "title": "招商银行历史测试半年报",
        "published_at": "2025-07-01T00:00:00+08:00",
        "source_official": True,
        "source_provider": "TEST_OFFICIAL",
        "document_url": "https://example.test/600036.pdf",
        "is_periodic_report_body": True,
        "category": "PERIODIC_REPORT",
    }
    write(root / "official-disclosure-pack.json", {
        "kind": "OFFICIAL_DISCLOSURE_PACK",
        "symbols_requested": ["600036.SH"],
        "results": [{"symbol": "600036.SH", "provider_status": "OK", "items": [report]}],
        "latest_periodic_report_refs": [report],
        "important_recent_refs": [],
    })
    if include_financial:
        write(root / "financial-reviews.json", {
            "600036.SH": {
                "status": "REVIEWED",
                "symbol": "600036.SH",
                "as_of": f"{date}T14:30:00+08:00",
                "source_report": "https://example.test/600036.pdf",
                "source_official": True,
                "period": "2025H1",
                "facts": [{"name": "净利润", "value": "TEST", "source": "官方半年报"}],
                "summary": "TEST_ONLY",
                "data_gaps": [],
            }
        })
    write(root / "news-research.json", {
        "status": "SEARCHED",
        "searched_at": f"{date}T14:40:00+08:00",
        "items": [{"symbols": ["600036.SH"], "title": "历史测试新闻",
                   "source": "TEST_NEWS", "published_at": f"{date}T10:00:00+08:00"}],
    })
    write(root / "candidate-research-pack.json", {
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": "LOW_RECOVERY",
        "cutoff_date": date,
        "selected_count": 1,
        "not_a_recommendation": True,
        "candidates": [{"symbol": "600036.SH", "name": "招商银行"}],
    })
    write(root / "universe-scope.json", {
        "authorized_symbols": ["600036.SH"],
        "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
        "not_full_a_share_claim": True,
    })


def buy_decision(req):
    row = req["market"]["600036.SH"][-1]
    d = decision_base(req)
    d.update(
        action="BUY",
        summary="TEST_ONLY research-only BUY proposal; no execution claimed.",
        order_proposal={
            "symbol": "600036.SH",
            "side": "BUY",
            "quantity": 100,
            "reference_price_cny": row["close"],
            "quote_time": req["context"]["information_cutoff"],
            "quote_source": row["source"],
        },
    )
    return d


@pytest.mark.parametrize("include_news", [False, True])
def test_research_only_can_prepare_on_last_available_session(repo, include_news):
    materialize(repo)
    setup_research(repo)
    data = one_symbol_data()
    data["time_travel_include_evidence"] = include_news
    assert data["sessions"][-1] == "2025-08-08"

    req = prepare_research_only_request(
        repo, "D02", "research-last-session", data, "2025-08-08"
    )
    assert req["context"]["submode"] == "RESEARCH_ONLY_TIME_TRAVEL"
    assert req["context"]["execution_time"] is None
    assert req["execution_status"] == "WAITING_FOR_REAL_NEXT_SESSION_DATA"
    assert req["research_input_manifest"]["variant_id"] == "D02"
    assert req["decision_research_bundle"]["coverage"]["financial_interpretation_completed"] == 1
    assert req["decision_research_bundle"]["coverage"]["news_verified"] == int(include_news)
    assert ("历史测试新闻" in req["prompt"]) == include_news
    assert ('"news_policy": "' + (
        "USE_ONLY_POINT_IN_TIME_ARCHIVED_NEWS" if include_news else "IGNORE_ARCHIVED_NEWS_BY_DEFAULT"
    ) + '"') in req["prompt"]
    assert "官方半年报" in req["prompt"]
    assert "NO_EXECUTION_UNTIL_REAL_NEXT_SESSION_DATA" in req["prompt"]


def test_research_only_buy_can_be_locked_without_execution(repo):
    materialize(repo)
    setup_research(repo)
    req = prepare_research_only_request(
        repo, "D02", "research-lock-buy", one_symbol_data(), "2025-08-08"
    )
    decision = buy_decision(req)
    assert validate_research_only_decision(repo, "D02", decision, req)
    lock = lock_research_only_decision(
        repo, "D02", "research-lock-buy", "2025-08-08", decision
    )
    assert lock["execution_status"] == "WAITING_FOR_REAL_NEXT_SESSION_DATA"
    assert lock["future_execution_data_seen"] is False
    root = repo / "runs/research-decisions/research-lock-buy/D02/2025-08-08"
    assert (root / "decision.json").exists()
    assert not (root / "execution.json").exists()


def test_research_only_buy_requires_completed_financial_review(repo):
    materialize(repo)
    setup_research(repo, include_financial=False)
    req = prepare_research_only_request(
        repo, "D02", "research-missing-financial", one_symbol_data(), "2025-08-08"
    )
    with pytest.raises(ValidationError, match="FINANCIAL_REVIEW_NOT_COMPLETED"):
        validate_research_only_decision(repo, "D02", buy_decision(req), req)


def test_research_only_decision_lock_is_immutable(repo):
    materialize(repo)
    setup_research(repo)
    req = prepare_research_only_request(
        repo, "D02", "research-lock-immutable", one_symbol_data(), "2025-08-08"
    )
    decision = buy_decision(req)
    first = lock_research_only_decision(
        repo, "D02", "research-lock-immutable", "2025-08-08", decision
    )
    second = lock_research_only_decision(
        repo, "D02", "research-lock-immutable", "2025-08-08", decision
    )
    assert first == second
    changed = copy.deepcopy(decision)
    changed["summary"] = "changed after lock"
    with pytest.raises(ValidationError, match="different content"):
        lock_research_only_decision(
            repo, "D02", "research-lock-immutable", "2025-08-08", changed
        )
