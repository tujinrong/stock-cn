"""Source adapters must not discard rights events while parsing raw OHLCV."""
from __future__ import annotations

import copy

import pytest

from stock_cn.sim_data import fetch_daily, source_corporate_action_hints, validate_dataset
from stock_cn.universe import fetch_candidate_history


def fetch_adapter(adapter, request):
    if adapter == "fixed":
        return fetch_daily(["600036.SH"], "2026-01-15", "2026-01-16", request)
    return fetch_candidate_history(
        {"rows": [{"symbol": "600036.SH", "name": "招商银行"}]},
        "2026-01-15", "2026-01-16", request=request, max_symbols=1,
    )


@pytest.mark.parametrize("adapter", ["fixed", "candidate"])
@pytest.mark.parametrize("as_list", [False, True])
def test_tencent_cash_rights_preserved_without_becoming_verified_ledger(adapter, as_list):
    event = {"nd": "2025", "fh_sh": "10.13", "djr": "2026-01-15",
             "cqr": "2026-01-16", "FHcontent": "10派10.13元"}
    rows = [
        ["2026-01-15", "40.00", "40.10", "40.20", "39.90", "100000"],
        ["2026-01-16", "39.10", "39.20", "39.30", "39.00", "110000",
         [event] if as_list else event],
    ]
    original = copy.deepcopy(rows)
    data, attempts = fetch_adapter(adapter, lambda url: {"data": {"sh600036": {"day": rows}}})
    assert rows == original
    assert attempts[0]["provider"] == "Tencent"
    bar = data["bars"]["2026-01-16"]["600036.SH"]
    assert bar["open"] == "39.10" and bar["volume"] == "110000"
    hint, = bar["corporate_action_hints"]
    assert all(hint[key] == value for key, value in event.items())
    assert hint["raw_source_payload"] == event
    assert hint["status"] == "UNVERIFIED_SOURCE_HINT"
    assert hint["information_available_at"] is None
    assert hint["row_date"] == "2026-01-16"
    assert hint["source"] == bar["source"]
    assert data["bars"]["2026-01-15"]["600036.SH"]["corporate_action_hints"] == []
    assert data["corporate_actions"] == []
    assert any("Historical information availability" in text for text in data["limitations"])
    validate_dataset(data)  # Historical research remains possible; execution checks hints separately.


def test_non_cash_and_unknown_nested_payloads_are_retained_as_unverified_hints():
    event = {"FHcontent": "10送10转10", "djr": "2026-07-30", "cqr": "2026-07-31",
             "future_schema_key": {"ratio": "2"}}
    row = ["2026-07-31", "10", "10", "10", "10", "1000", [event, ["UNKNOWN_EVENT"]]]
    hints = source_corporate_action_hints(row, "Tencent", "https://example.test/source")
    assert len(hints) == 2
    assert hints[0]["FHcontent"] == "10送10转10"
    assert hints[0]["future_schema_key"] == {"ratio": "2"}
    assert hints[1]["raw_payload"] == "UNKNOWN_EVENT"
    assert all(h["status"] == "UNVERIFIED_SOURCE_HINT" and h["information_available_at"] is None for h in hints)
    hints[0]["future_schema_key"]["ratio"] = "99"
    assert event["future_schema_key"]["ratio"] == "2"


@pytest.mark.parametrize("adapter", ["fixed", "candidate"])
def test_eastmoney_turnover_is_not_interpreted_as_corporate_action(adapter):
    def request(url):
        if "gtimg" in url:
            raise OSError("test primary outage")
        return {"data": {"klines": [
            "2026-01-15,40.00,40.10,40.20,39.90,1000,40000",
            "2026-01-16,40.10,40.20,40.30,40.00,1100,44220",
        ]}}

    data, attempts = fetch_adapter(adapter, request)
    assert attempts[0]["provider"] == "Eastmoney"
    assert all(bar["corporate_action_hints"] == []
               for bars in data["bars"].values() for bar in bars.values())
