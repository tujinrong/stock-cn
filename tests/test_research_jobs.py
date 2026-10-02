import json
from pathlib import Path

import pytest

from stock_cn.research_jobs import (
    ingest_research_answer,
    prepare_research_job,
    validate_research_answer,
)
from stock_cn.research_inputs import load_research_inputs


def official():
    report = {
        "symbol": "600036.SH",
        "title": "招商银行2026年半年度报告",
        "published_at": "2026-08-29T00:00:00+08:00",
        "source_official": True,
        "source_provider": "CNINFO",
        "document_url": "https://static.cninfo.com.cn/report.pdf",
        "is_periodic_report_body": True,
        "category": "PERIODIC_REPORT",
    }
    return {
        "kind": "OFFICIAL_DISCLOSURE_PACK",
        "provider": "CNINFO",
        "provider_official": True,
        "results": [{
            "symbol": "600036.SH",
            "provider_status": "OK",
            "items": [report],
        }],
        "symbols_requested": ["600036.SH"],
        "latest_periodic_report_refs": [report],
        "important_recent_refs": [],
    }


def answer():
    return {
        "financial_reviews": {
            "600036.SH": {
                "status": "REVIEWED",
                "symbol": "600036.SH",
                "as_of": "2026-10-08T10:50:00+08:00",
                "source_report": "https://static.cninfo.com.cn/report.pdf",
                "source_official": True,
                "period": "2026H1",
                "facts": [{
                    "name": "净利润",
                    "value": "TEST",
                    "source": "官方半年报",
                }],
                "summary": "TEST_ONLY",
                "data_gaps": [],
            }
        },
        "news_research": {
            "status": "SEARCHED",
            "searched_at": "2026-10-08T10:52:00+08:00",
            "items": [{
                "symbols": ["600036.SH"],
                "title": "测试新闻",
                "published_at": "2026-10-08T09:00:00+08:00",
                "source": "TEST_MEDIA",
                "url": "https://example.test/news",
                "material_fact": False,
            }],
        },
    }


def request(tmp_path):
    return prepare_research_job(
        tmp_path,
        job_id="job-001",
        variant_id="D02",
        decision_date="2026-10-08",
        information_cutoff="2026-10-08T11:00:00+08:00",
        mode="FORMAL",
        symbols=["600036.SH"],
        official_disclosure_pack=official(),
        candidate_research_pack={
            "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
            "purpose": "LOW_RECOVERY",
            "cutoff_date": "2026-10-08",
            "selected_count": 1,
            "not_a_recommendation": True,
            "candidates": [{"symbol": "600036.SH", "name": "招商银行"}],
        },
        universe_scope={
            "authorized_symbols": ["600036.SH"],
            "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
        },
    )


def test_prepare_research_job_contains_no_trade_instruction(tmp_path):
    req = request(tmp_path)
    assert req["formal_execution"] is False
    assert req["required_outputs"]["financial_reviews"]
    text = (tmp_path / "runs/research/jobs/job-001/ai_task.md").read_text()
    assert "不做交易" in text
    assert "financial_reviews" in text
    assert (tmp_path / "runs/research/jobs/job-001/request.json").exists()


def test_validate_answer_requires_full_symbol_coverage(tmp_path):
    req = request(tmp_path)
    bad = answer()
    bad["financial_reviews"] = {}
    with pytest.raises(ValueError, match="coverage mismatch"):
        validate_research_answer(bad, req)


def test_validate_answer_rejects_future_news(tmp_path):
    req = request(tmp_path)
    bad = answer()
    bad["news_research"]["items"][0]["published_at"] = "2026-10-08T12:00:00+08:00"
    with pytest.raises(ValueError, match="future research evidence"):
        validate_research_answer(bad, req)


def test_ingest_answer_writes_research_inputs_only(tmp_path):
    request(tmp_path)
    holdings = tmp_path / "strategies/D/variants/D02/holdings.json"
    holdings.parent.mkdir(parents=True, exist_ok=True)
    holdings.write_text('{"sentinel":"UNCHANGED"}\n', encoding="utf-8")

    result = ingest_research_answer(tmp_path, "job-001", answer())
    assert result["trade_executed"] is False
    assert result["holdings_changed"] is False
    assert holdings.read_text(encoding="utf-8") == '{"sentinel":"UNCHANGED"}\n'

    root = tmp_path / "research-inputs/D02/2026-10-08"
    assert (root / "financial-reviews.json").exists()
    assert (root / "news-research.json").exists()
    bundle = load_research_inputs(
        tmp_path, "D02", "2026-10-08",
        as_of="2026-10-08T11:00:00+08:00",
    )
    assert bundle["financial_reviews"]["600036.SH"]["status"] == "REVIEWED"


def test_ingest_is_idempotent_and_conflict_safe(tmp_path):
    request(tmp_path)
    first = ingest_research_answer(tmp_path, "job-001", answer())
    second = ingest_research_answer(tmp_path, "job-001", answer())
    assert first["answer_sha256"] == second["answer_sha256"]

    changed = answer()
    changed["financial_reviews"]["600036.SH"]["summary"] = "CHANGED"
    with pytest.raises(ValueError, match="different content"):
        ingest_research_answer(tmp_path, "job-001", changed)


def test_prepared_request_tamper_is_rejected(tmp_path):
    request(tmp_path)
    p = tmp_path / "runs/research/jobs/job-001/request.json"
    obj = json.loads(p.read_text())
    obj["symbols"] = ["600900.SH"]
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="request changed"):
        ingest_research_answer(tmp_path, "job-001", answer())
