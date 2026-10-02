from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from stock_cn.evidence import (
    CNINFO_ANNOUNCEMENTS,
    CNINFO_TOP_SEARCH,
    EvidenceProviderError,
    build_official_disclosure_pack,
    classify_announcement_title,
    fetch_cninfo_announcements,
    is_periodic_report_body,
    resolve_cninfo_org_id,
)


CN = ZoneInfo("Asia/Shanghai")


def ms(text):
    dt = datetime.fromisoformat(text)
    return int(dt.astimezone(timezone.utc).timestamp() * 1000)


def fake_post(url, form):
    if url == CNINFO_TOP_SEARCH:
        code = form["keyWord"]
        return [{"key": code, "code": "gssh0" + code, "zwjc": "测试公司"}]
    if url == CNINFO_ANNOUNCEMENTS:
        page = int(form["pageNum"])
        if page == 1:
            return {
                "hasMore": True,
                "announcements": [
                    {
                        "announcementId": "r1",
                        "secName": "测试公司",
                        "announcementTitle": "<em>2026年半年度报告</em>",
                        "announcementTime": ms("2026-08-28T18:00:00+08:00"),
                        "adjunctUrl": "finalpage/2026-08-28/report.pdf",
                    },
                    {
                        "announcementId": "r1-dup",
                        "secName": "测试公司",
                        "announcementTitle": "2026年半年度报告",
                        "announcementTime": ms("2026-08-28T18:10:00+08:00"),
                        "adjunctUrl": "finalpage/2026-08-28/report.pdf",
                    },
                    {
                        "announcementId": "future",
                        "secName": "测试公司",
                        "announcementTitle": "关于回购股份的公告",
                        "announcementTime": ms("2026-10-05T09:00:00+08:00"),
                        "adjunctUrl": "finalpage/2026-10-05/future.pdf",
                    },
                ],
            }
        if page == 2:
            return {
                "hasMore": False,
                "announcements": [
                    {
                        "announcementId": "b1",
                        "secName": "测试公司",
                        "announcementTitle": "关于回购公司股份方案的公告",
                        "announcementTime": ms("2026-09-20T17:00:00+08:00"),
                        "adjunctUrl": "/finalpage/2026-09-20/buyback.pdf",
                    },
                    {
                        "announcementId": "risk1",
                        "secName": "测试公司",
                        "announcementTitle": "关于收到监管措施的公告",
                        "announcementTime": ms("2026-09-21T17:00:00+08:00"),
                        "adjunctUrl": "/finalpage/2026-09-21/risk.pdf",
                    },
                ],
            }
    raise AssertionError(f"unexpected URL: {url}")


def test_title_classification_is_research_routing_not_sentiment():
    assert classify_announcement_title("2026年半年度报告") == "PERIODIC_REPORT"
    assert classify_announcement_title("关于回购股份的公告") == "BUYBACK"
    assert classify_announcement_title("关于收到监管措施的公告") == "RISK"
    assert classify_announcement_title("日常经营情况说明") == "OTHER"


def test_periodic_report_body_excludes_summary_and_audit_material():
    assert is_periodic_report_body("2026年半年度报告")
    assert not is_periodic_report_body("2026年半年度报告摘要")
    assert not is_periodic_report_body("2026年年度报告审计报告")


def test_org_id_resolver_supports_current_topsearch_shape():
    assert resolve_cninfo_org_id("600036.SH", fake_post) == "gssh0600036"


def test_cninfo_fetch_paginates_filters_future_and_deduplicates():
    out = fetch_cninfo_announcements(
        "600036.SH", "2026-08-01", "2026-10-31",
        as_of="2026-10-03T11:00:00+08:00",
        max_pages=3, post_json=fake_post,
    )
    assert out["provider_status"] == "OK"
    assert out["pages_used"] == 2
    assert out["provider_rows"] == 5
    assert out["future_items_filtered"] == 1
    # duplicate half-year report records collapse to one causal record
    titles = [x["title"] for x in out["items"]]
    assert titles.count("2026年半年度报告") == 1
    assert "关于回购股份的公告" not in titles  # future item
    assert "关于回购公司股份方案的公告" in titles
    report = next(x for x in out["items"] if x["title"] == "2026年半年度报告")
    assert report["is_periodic_report_body"] is True
    assert report["document_url"].startswith("https://static.cninfo.com.cn/")
    assert report["source_official"] is True
    assert report["research_meaning"] == "OFFICIAL_DISCLOSURE_REFERENCE_NOT_FINANCIAL_CONCLUSION"


def test_empty_is_different_from_provider_failure():
    def empty_post(url, form):
        if url == CNINFO_TOP_SEARCH:
            return [{"key": form["keyWord"], "code": "gssh0" + form["keyWord"]}]
        return {"hasMore": False, "announcements": []}

    empty = fetch_cninfo_announcements(
        "600036.SH", "2026-09-01", "2026-09-30", post_json=empty_post
    )
    assert empty["provider_status"] == "EMPTY"
    assert empty["items"] == []

    def failed_post(url, form):
        raise RuntimeError("provider offline")

    pack = build_official_disclosure_pack(
        ["600036.SH"], "2026-09-01", "2026-09-30", post_json=failed_post
    )
    assert pack["complete_for_requested_symbols"] is False
    assert pack["symbols_failed"] == ["600036.SH"]
    assert pack["results"][0]["provider_status"] == "FAILED"
    assert "provider offline" in pack["results"][0]["error"]
    assert "must never be interpreted" in pack["failure_semantics"]


def test_pack_extracts_periodic_and_important_refs_without_financial_conclusion():
    pack = build_official_disclosure_pack(
        ["600036.SH"], "2026-08-01", "2026-10-31",
        as_of="2026-10-03T11:00:00+08:00", post_json=fake_post
    )
    assert pack["complete_for_requested_symbols"] is True
    assert any(x["title"] == "2026年半年度报告"
               for x in pack["latest_periodic_report_refs"])
    cats = {x["category"] for x in pack["important_recent_refs"]}
    assert {"BUYBACK", "RISK"} <= cats
    assert pack["financial_conclusions_extracted"] is False
    assert pack["metadata_only"] is True
    assert pack["news_research_required"] is True


def test_excluded_or_unsupported_board_rejected_before_provider_call():
    called = False
    def never(url, form):
        nonlocal called
        called = True
        return []
    with pytest.raises(ValueError, match="unsupported"):
        resolve_cninfo_org_id("688001.SH", never)
    assert called is False
