from copy import deepcopy

import pytest

from stock_cn.research_bundle import (
    build_decision_research_bundle,
    buy_research_preflight,
)


def official_pack(status="OK"):
    report = {
        "symbol": "600036.SH",
        "title": "招商银行股份有限公司2026年半年度报告",
        "published_at": "2026-08-29T00:00:00+08:00",
        "source_official": True,
        "source_provider": "CNINFO",
        "document_url": "https://static.cninfo.com.cn/report.pdf",
        "is_periodic_report_body": True,
        "category": "PERIODIC_REPORT",
    }
    return {
        "kind": "OFFICIAL_DISCLOSURE_PACK",
        "results": [{
            "symbol": "600036.SH",
            "provider_status": status,
            "items": [] if status != "OK" else [report],
        }],
        "latest_periodic_report_refs": [] if status != "OK" else [report],
        "important_recent_refs": [],
    }


def financial_review(status="REVIEWED"):
    return {
        "status": status,
        "as_of": "2026-10-08T10:50:00+08:00",
        "source_report": "https://static.cninfo.com.cn/report.pdf",
        "source_official": True,
        "period": "2026H1",
        "facts": [
            {"name": "review_completed", "value": True, "source": "official report"}
        ],
        "summary": "TEST_ONLY financial review fixture",
        "data_gaps": [],
    }


def news(status="SEARCHED"):
    return {
        "status": status,
        "as_of": "2026-10-08T10:55:00+08:00",
        "items": [{
            "symbols": ["600036.SH"],
            "title": "测试新闻",
            "published_at": "2026-10-08T09:00:00+08:00",
            "source": "TEST_MEDIA",
            "url": "https://example.test/news",
        }] if status == "SEARCHED" else [],
    }


def test_research_bundle_maps_official_financial_and_news_coverage():
    bundle = build_decision_research_bundle(
        ["600036.SH"],
        as_of="2026-10-08T11:00:00+08:00",
        official_disclosure_pack=official_pack(),
        financial_reviews={"600036.SH": financial_review()},
        news_research=news(),
        market_context={"mode": "FORMAL"},
    )
    row = bundle["per_symbol"][0]
    assert row["official_disclosure_status"] == "OK"
    assert row["latest_periodic_report_ref"]["title"].endswith("半年度报告")
    assert row["financial_review_status"] == "REVIEWED"
    assert row["recent_news_status"] == "SEARCHED"
    assert row["data_gaps"] == []
    assert bundle["coverage_is_not_a_score"] is True
    assert buy_research_preflight(bundle, "600036.SH")["ready"] is True


def test_failed_provider_and_unchecked_news_are_gaps_not_good_news():
    bundle = build_decision_research_bundle(
        ["600036.SH"],
        as_of="2026-10-08T11:00:00+08:00",
        official_disclosure_pack=official_pack("FAILED"),
        news_research={"status": "UNAVAILABLE", "items": []},
    )
    row = bundle["per_symbol"][0]
    assert "OFFICIAL_DISCLOSURE_PROVIDER_FAILED" in row["data_gaps"]
    assert "RECENT_NEWS_NOT_VERIFIED" in row["data_gaps"]
    preflight = buy_research_preflight(bundle, "600036.SH")
    assert preflight["ready"] is False
    assert "OFFICIAL_DISCLOSURE_NOT_SUCCESSFULLY_CHECKED" in preflight["reasons"]
    assert "FINANCIAL_REVIEW_NOT_COMPLETED" in preflight["reasons"]


def test_report_reference_alone_does_not_count_as_financial_review():
    bundle = build_decision_research_bundle(
        ["600036.SH"],
        as_of="2026-10-08T11:00:00+08:00",
        official_disclosure_pack=official_pack(),
        news_research=news(),
    )
    row = bundle["per_symbol"][0]
    assert row["financial_review_status"] == "REPORT_REFERENCE_AVAILABLE_REVIEW_REQUIRED"
    preflight = buy_research_preflight(bundle, "600036.SH")
    assert not preflight["ready"]
    assert "FINANCIAL_REVIEW_NOT_COMPLETED" in preflight["reasons"]


def test_future_news_or_future_financial_review_is_rejected():
    future_news = news()
    future_news["items"][0]["published_at"] = "2026-10-08T12:00:00+08:00"
    with pytest.raises(ValueError, match="future research evidence"):
        build_decision_research_bundle(
            ["600036.SH"],
            as_of="2026-10-08T11:00:00+08:00",
            official_disclosure_pack=official_pack(),
            financial_reviews={"600036.SH": financial_review()},
            news_research=future_news,
        )

    review = financial_review()
    review["as_of"] = "2026-10-08T11:01:00+08:00"
    with pytest.raises(ValueError, match="future financial review"):
        build_decision_research_bundle(
            ["600036.SH"],
            as_of="2026-10-08T11:00:00+08:00",
            official_disclosure_pack=official_pack(),
            financial_reviews={"600036.SH": review},
            news_research=news(),
        )


def test_candidate_pack_must_be_subset_of_researched_symbols():
    pack = {
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "candidates": [{"symbol": "600900.SH"}],
    }
    with pytest.raises(ValueError, match="outside research bundle"):
        build_decision_research_bundle(
            ["600036.SH"],
            as_of="2026-10-08T11:00:00+08:00",
            official_disclosure_pack=official_pack(),
            candidate_research_pack=pack,
            financial_reviews={"600036.SH": financial_review()},
            news_research=news(),
        )


def test_missing_bundle_or_symbol_blocks_buy_preflight():
    assert buy_research_preflight(None, "600036.SH")["ready"] is False
    bundle = build_decision_research_bundle(
        ["600036.SH"],
        as_of="2026-10-08T11:00:00+08:00",
        official_disclosure_pack=official_pack(),
        financial_reviews={"600036.SH": financial_review()},
        news_research=news(),
    )
    result = buy_research_preflight(bundle, "600900.SH")
    assert result["reasons"] == ["SYMBOL_RESEARCH_MISSING"]
