import json
from pathlib import Path

import pytest

from stock_cn.research_inputs import attach_research_inputs, load_research_inputs


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def manifest():
    return {
        "variant_id": "D02",
        "mode": "FORMAL",
        "decision_date": "2026-10-08",
        "information_cutoff": "2026-10-08T10:55:00+08:00",
        "source_commit": "TEST",
        "formal_execution": False,
    }


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
        "symbols_requested": ["600036.SH"],
        "results": [{
            "symbol": "600036.SH",
            "provider_status": "OK",
            "items": [report],
        }],
        "latest_periodic_report_refs": [report],
        "important_recent_refs": [],
    }


def financials():
    return {
        "600036.SH": {
            "status": "REVIEWED",
            "symbol": "600036.SH",
            "as_of": "2026-10-08T10:50:00+08:00",
            "source_report": "https://static.cninfo.com.cn/report.pdf",
            "source_official": True,
            "period": "2026H1",
            "facts": [{"name": "净利润", "value": "TEST", "source": "官方半年报"}],
            "summary": "TEST_ONLY",
            "data_gaps": [],
        }
    }


def news():
    return {
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
    }


def candidate_pack():
    return {
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": "LOW_RECOVERY",
        "cutoff_date": "2026-10-08",
        "selected_count": 1,
        "not_a_recommendation": True,
        "candidates": [{"symbol": "600036.SH", "name": "招商银行"}],
    }


def setup_files(tmp_path):
    root = tmp_path / "research-inputs/D02/2026-10-08"
    write(root / "manifest.json", manifest())
    write(root / "official-disclosure-pack.json", official())
    write(root / "financial-reviews.json", financials())
    write(root / "news-research.json", news())
    write(root / "candidate-research-pack.json", candidate_pack())
    write(root / "universe-scope.json", {
        "authorized_symbols": ["600036.SH"],
        "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
        "not_full_a_share_claim": True,
    })
    return root


def test_load_complete_research_input_bundle(tmp_path):
    setup_files(tmp_path)
    bundle = load_research_inputs(
        tmp_path, "D02", "2026-10-08",
        as_of="2026-10-08T11:00:00+08:00",
    )
    assert bundle["kind"] == "FILE_RESEARCH_INPUT_BUNDLE"
    assert bundle["missing_files"] == []
    assert bundle["financial_reviews"]["600036.SH"]["source_official"] is True
    assert bundle["news_research"]["status"] == "SEARCHED"
    assert len(bundle["file_sha256"]) == 6


def test_missing_optional_files_remain_explicit_gaps(tmp_path):
    root = tmp_path / "research-inputs/D02/2026-10-08"
    write(root / "manifest.json", manifest())
    bundle = load_research_inputs(
        tmp_path, "D02", "2026-10-08",
        as_of="2026-10-08T11:00:00+08:00",
    )
    assert "financial-reviews.json" in bundle["missing_files"]
    assert bundle["news_research"]["status"] == "NOT_CHECKED"


def test_future_research_manifest_is_rejected(tmp_path):
    setup_files(tmp_path)
    p = tmp_path / "research-inputs/D02/2026-10-08/manifest.json"
    obj = json.loads(p.read_text())
    obj["information_cutoff"] = "2026-10-08T11:01:00+08:00"
    write(p, obj)
    with pytest.raises(ValueError, match="future"):
        load_research_inputs(
            tmp_path, "D02", "2026-10-08",
            as_of="2026-10-08T11:00:00+08:00",
        )


def test_candidate_pack_cannot_escape_universe_scope(tmp_path):
    setup_files(tmp_path)
    p = tmp_path / "research-inputs/D02/2026-10-08/universe-scope.json"
    write(p, {"authorized_symbols": ["600900.SH"]})
    with pytest.raises(ValueError, match="outside authorized universe"):
        load_research_inputs(
            tmp_path, "D02", "2026-10-08",
            as_of="2026-10-08T11:00:00+08:00",
        )


def test_unofficial_financial_review_rejected(tmp_path):
    setup_files(tmp_path)
    p = tmp_path / "research-inputs/D02/2026-10-08/financial-reviews.json"
    obj = financials()
    obj["600036.SH"]["source_official"] = False
    write(p, obj)
    with pytest.raises(ValueError, match="official source"):
        load_research_inputs(
            tmp_path, "D02", "2026-10-08",
            as_of="2026-10-08T11:00:00+08:00",
        )


def test_attach_research_inputs_refuses_silent_conflict(tmp_path):
    setup_files(tmp_path)
    bundle = load_research_inputs(
        tmp_path, "D02", "2026-10-08",
        as_of="2026-10-08T11:00:00+08:00",
    )
    snapshot = {
        "market_date": "2026-10-08",
        "news_research": {"status": "NO_RELEVANT_RECENT_NEWS", "items": []},
    }
    with pytest.raises(ValueError, match="conflicts"):
        attach_research_inputs(snapshot, bundle)


def test_attach_research_inputs_adds_manifest_provenance(tmp_path):
    setup_files(tmp_path)
    bundle = load_research_inputs(
        tmp_path, "D02", "2026-10-08",
        as_of="2026-10-08T11:00:00+08:00",
    )
    snapshot = {"market_date": "2026-10-08"}
    enriched = attach_research_inputs(snapshot, bundle)
    assert enriched["financial_reviews"]["600036.SH"]["status"] == "REVIEWED"
    assert enriched["research_input_manifest"]["variant_id"] == "D02"
    assert "financial-reviews.json" in enriched["research_input_manifest"]["file_sha256"]
