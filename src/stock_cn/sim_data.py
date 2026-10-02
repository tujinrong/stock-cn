"""Bounded, unadjusted daily data for simulation; never a real-time feed."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SYMBOLS = {
    "600036.SH": "招商银行", "002594.SZ": "比亚迪", "600660.SH": "福耀玻璃",
    "600900.SH": "长江电力", "601100.SH": "恒立液压",
}


def number(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not money")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("invalid numeric value") from exc
    if not result.is_finite():
        raise ValueError("non-finite numeric value")
    return result


def load_dataset(path):
    """Validate first; explicit sessions avoid inventing a weekday-only calendar."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_dataset(data)
    return data


def validate_dataset(data):
    if data.get("kind") not in {"TEST_ONLY", "REAL_HISTORY"}:
        raise ValueError("dataset.kind must identify real history or TEST_ONLY")
    if data.get("price_basis") != "unadjusted":
        raise ValueError("execution requires unadjusted prices")
    days = data["sessions"]
    if len(days) < 2 or days != sorted(set(days)):
        raise ValueError("at least two unique, increasing market sessions required")
    for day in days:
        date.fromisoformat(day)
        if day not in data["bars"]:
            raise ValueError(f"missing session: {day}")
    for symbol, meta in data["instruments"].items():
        if len(symbol) != 9 or symbol[-3:] not in {".SH", ".SZ"}:
            raise ValueError("invalid instrument identifier")
        # This MVP deliberately only supports verified ordinary main-board shares.
        if meta.get("board") != "MAIN" or symbol.startswith(("688", "689", "300", "301")):
            raise ValueError("unsupported/excluded board; STAR is always excluded")
        prefixes = ("600", "601", "603", "605") if symbol.endswith(".SH") else ("000", "001", "002", "003")
        if not symbol.startswith(prefixes):
            raise ValueError("market/code mismatch or unsupported security type")
        if meta.get("lot_size") != 100 or not meta.get("name"):
            raise ValueError("unsupported instrument metadata")
    for day in days:
        for symbol, bar in data["bars"][day].items():
            if symbol not in data["instruments"] or not bar.get("source"):
                raise ValueError("unknown symbol or missing provenance")
            if number(bar["open"]) <= 0 or number(bar["close"]) <= 0:
                raise ValueError("prices must be positive")
            for key in ("open", "close", "limit_up", "limit_down"):
                if bar.get(key) is not None and number(bar[key]) * 100 != (number(bar[key]) * 100).to_integral_value():
                    raise ValueError("price not on the 0.01 tick")
    for item in data.get("evidence", []):
        ts = datetime.fromisoformat(item["published_at"])
        if ts.tzinfo is None or not item.get("source"):
            raise ValueError("evidence needs aware publication time and source")
    if data.get("corporate_actions"):
        # No silent handling of dividends/splits: require a separately validated adapter.
        raise ValueError("corporate actions require verified processing; interval not supported yet")
    if data["kind"] == "REAL_HISTORY" and not data.get("limitations"):
        raise ValueError("real history requires a declared coverage/rights-event limitation")


def request_json(url, timeout=12):
    req = Request(url, headers={"User-Agent": "stock-cn-simulation/0.4"})
    with urlopen(req, timeout=timeout) as response:
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("response size limit exceeded")
    return json.loads(raw.decode("utf-8"))


def fetch_daily(symbols, start, end, request=request_json):
    """One Tencent request per symbol, Eastmoney fallback; no retries without limit.

    Data is a temporary input, not committed as a market database. The returned
    interval is FLOW_ONLY until calendar and corporate events are independently verified.
    """
    date.fromisoformat(start)
    date.fromisoformat(end)
    if end < start or len(symbols) > 10:
        raise ValueError("invalid interval or more than 10 requested symbols")
    if (date.fromisoformat(end) - date.fromisoformat(start)).days > 180:
        raise ValueError("probe/replay request limited to 180 calendar days")
    output, attempts = {}, []
    for symbol in symbols:
        if symbol not in SYMBOLS:
            raise ValueError("source probe limited to the five configured, known instruments")
        code, exchange = symbol.split(".")
        tx_symbol = exchange.lower() + code
        tx_url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urlencode({
            "param": f"{tx_symbol},day,{start},{end},320,"})
        em_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urlencode({
            "secid": f"{1 if exchange == 'SH' else 0}.{code}", "klt": 101, "fqt": 0,
            "beg": start.replace("-", ""), "end": end.replace("-", ""),
            "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57"})
        errors = []
        for provider, url in (("Tencent", tx_url), ("Eastmoney", em_url)):
            try:
                payload = request(url)
                if provider == "Tencent":
                    # Never silently take qfqday/hfqday as executable raw prices.
                    rows = payload["data"][tx_symbol]["day"]
                else:
                    rows = [x.split(",") for x in payload["data"]["klines"]]
                selected = {x[0]: {"open": str(number(x[1])), "close": str(number(x[2])),
                                      "source": url, "provider": provider}
                            for x in rows if start <= x[0] <= end}
                if len(selected) < 2:
                    raise ValueError("insufficient returned sessions")
                output[symbol] = selected
                attempts.append({"symbol": symbol, "provider": provider, "status": "OK",
                                 "first_date": min(selected), "last_date": max(selected),
                                 "rows": len(selected), "fallback_errors": errors})
                break
            except Exception as exc:
                errors.append({"provider": provider, "error": f"{type(exc).__name__}: {exc}"[:500]})
        else:
            attempts.append({"symbol": symbol, "status": "FAILED", "errors": errors})
    if len(output) != len(symbols):
        return None, attempts
    sets = [set(rows) for rows in output.values()]
    common = set.intersection(*sets)
    union = set.union(*sets)
    sessions = sorted(union)
    data = {"schema_version": "0.4", "kind": "REAL_HISTORY", "price_basis": "unadjusted",
            "fidelity": "FLOW_ONLY_REAL_PRICES", "sessions": sessions,
            "calendar_source": "returned provider sessions; not independently certified",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "limitations": ["No archived intraday/news/fundamental verification.",
                            "Previous close decision, next open execution; not 11:00 replay.",
                            "Corporate actions not verified; not investment-performance evidence.",
                            f"Missing-symbol sessions are preserved and rejected, not dropped: {len(union-common)}"],
            "instruments": {s: {"name": SYMBOLS[s], "board": "MAIN", "lot_size": 100} for s in symbols},
            "bars": {d: {s: output[s][d] for s in symbols if d in output[s]} for d in sessions},
            "evidence": [], "corporate_actions": []}
    validate_dataset(data)
    return data, attempts


def fixture():
    """Explicit synthetic prices for deterministic engineering tests, never returns evidence."""
    days = ["2025-08-01", "2025-08-04", "2025-08-05", "2025-08-06", "2025-08-07", "2025-08-08"]
    prices = [40, 90, 50, 28, 100]
    bars = {}
    for i, day in enumerate(days):
        bars[day] = {s: {"open": str(number(p) + number(i) / 10),
                         "close": str(number(p) + number(i) / 5),
                         "source": "TEST_ONLY:synthetic-v1", "suspended": False,
                         "limit_down": str(number(p) * Decimal("0.9")),
                         "limit_up": str(number(p) * Decimal("1.1"))}
                     for s, p in zip(SYMBOLS, prices)}
    return {"schema_version": "0.4", "kind": "TEST_ONLY", "price_basis": "unadjusted",
            "fidelity": "ENGINEERING_ONLY", "sessions": days,
            "calendar_source": "explicit synthetic test sessions", "bars": bars,
            "instruments": {s: {"name": n, "board": "MAIN", "lot_size": 100} for s, n in SYMBOLS.items()},
            "evidence": [], "corporate_actions": [],
            "limitations": ["Synthetic prices and scripted decisions; not an AI investment test."]}
