"""Bounded A-share universe discovery for AI_SELECT strategies.

This module is a research pre-filter, never an investment rule. It reduces a broad
A-share list to a bounded candidate set before deeper point-in-time K-line analysis.
STAR Market is excluded. Current project constraints also exclude unsupported
ChiNext/unknown boards until explicitly enabled and tested.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode

from .sim_data import number, request_json, validate_dataset

EASTMONEY_CLIST = "https://push2.eastmoney.com/api/qt/clist/get"

SH_MAIN_PREFIXES = ("600", "601", "603", "605")
SZ_MAIN_PREFIXES = ("000", "001", "002", "003")


def _eligible(code, market):
    if not isinstance(code, str) or len(code) != 6:
        return False
    if market == 1:
        return code.startswith(SH_MAIN_PREFIXES)
    if market == 0:
        return code.startswith(SZ_MAIN_PREFIXES)
    return False


def _symbol(code, market):
    return code + (".SH" if market == 1 else ".SZ")


def fetch_live_universe(request=request_json, *, page_size=100, max_pages=60):
    """Fetch a current broad A-share cross section from Eastmoney.

    The public list endpoint is paged conservatively because large single-page
    requests may be truncated. This is a current discovery adapter, not a
    historical universe archive.
    """
    if not 20 <= page_size <= 200 or not 1 <= max_pages <= 100:
        raise ValueError("invalid paging budget")
    all_rows = {}
    total = None
    pages = 0
    source_urls = []
    for page in range(1, max_pages + 1):
        url = EASTMONEY_CLIST + "?" + urlencode({
            "pn": page, "pz": page_size, "po": 1, "np": 1, "fltt": 2, "invt": 2,
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f6,f8,f12,f13,f14,f20,f21",
        })
        payload = request(url)
        data = payload.get("data") or {}
        if total is None:
            total = data.get("total")
        diff = data.get("diff") or []
        if isinstance(diff, dict):
            page_rows = list(diff.values())
        elif isinstance(diff, list):
            page_rows = diff
        else:
            raise ValueError("unexpected universe payload")
        if not page_rows:
            break
        before = len(all_rows)
        for row in page_rows:
            code = str(row.get("f12", ""))
            try:
                market = int(row.get("f13"))
            except (TypeError, ValueError):
                continue
            key = (market, code)
            all_rows[key] = row
        pages += 1
        source_urls.append(url)
        if len(all_rows) == before:
            break
        if total is not None:
            try:
                if len(all_rows) >= int(total):
                    break
            except (TypeError, ValueError):
                pass

    out = []
    for (_, _), row in all_rows.items():
        code, market = str(row.get("f12", "")), row.get("f13")
        try:
            market = int(market)
        except (TypeError, ValueError):
            continue
        if not _eligible(code, market):
            continue
        name = str(row.get("f14") or "").strip()
        if not name:
            continue
        def dec(key):
            value = row.get(key)
            if value in (None, "", "-"):
                return None
            try:
                return str(number(value))
            except ValueError:
                return None
        out.append({
            "symbol": _symbol(code, market),
            "name": name,
            "price_cny": dec("f2"),
            "change_pct": dec("f3"),
            "amount_cny": dec("f6"),
            "turnover_rate_pct": dec("f8"),
            "market_cap_cny": dec("f20"),
            "float_market_cap_cny": dec("f21"),
            "risk_tags": [tag for tag, cond in (
                ("ST_NAME", "ST" in name.upper()),
                ("SPECIAL_NAME", name.startswith(("N", "C"))),
            ) if cond],
        })
    if len(out) < 100:
        raise ValueError(
            f"unexpectedly small eligible universe: eligible={len(out)} "
            f"raw_unique={len(all_rows)} total={total} pages={pages}"
        )
    return {
        "kind": "CURRENT_UNIVERSE_SNAPSHOT",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": EASTMONEY_CLIST,
        "source_pages": pages,
        "source_last_url": source_urls[-1] if source_urls else None,
        "scope": "SH/SZ ordinary main-board prefixes supported by current project; STAR and unsupported boards excluded",
        "total_provider_rows": total,
        "raw_unique_rows": len(all_rows),
        "eligible_count": len(out),
        "rows": out,
    }


def _rank_numeric(rows, key, reverse=True):
    valid = [r for r in rows if r.get(key) is not None]
    return sorted(valid, key=lambda r: number(r[key]), reverse=reverse)


def bounded_prefilter(snapshot, purpose, *, max_candidates=60):
    """Reduce thousands of names to a bounded research set.

    The result is only a compute-budget gate. AI must not treat inclusion/rank as a
    recommendation or as proof of quality.
    """
    if snapshot.get("kind") != "CURRENT_UNIVERSE_SNAPSHOT":
        raise ValueError("current universe snapshot required")
    if type(max_candidates) is not int or not 10 <= max_candidates <= 100:
        raise ValueError("candidate budget must be 10..100")
    rows = [r for r in snapshot["rows"]
            if r.get("price_cny") is not None and r.get("amount_cny") is not None]
    if purpose == "LOW_RECOVERY":
        # A broad liquid/size seed; low-position/recovery is evaluated only after
        # fetching each candidate's own historical prefix.
        liquid = _rank_numeric(rows, "amount_cny")[:max_candidates * 2]
        sized = _rank_numeric(rows, "market_cap_cny")[:max_candidates * 2]
        ordered = []
        for r in liquid + sized:
            if r["symbol"] not in {x["symbol"] for x in ordered}:
                ordered.append(r)
            if len(ordered) >= max_candidates:
                break
    elif purpose == "ABNORMAL_DROP":
        losers = _rank_numeric(rows, "change_pct", reverse=False)[:max_candidates // 2]
        liquid = _rank_numeric(rows, "amount_cny")[:max_candidates]
        ordered = []
        for r in losers + liquid:
            if r["symbol"] not in {x["symbol"] for x in ordered}:
                ordered.append(r)
            if len(ordered) >= max_candidates:
                break
    else:
        raise ValueError("unknown prefilter purpose")
    return {
        "kind": "BOUNDED_CANDIDATE_SEED",
        "purpose": purpose,
        "max_candidates": max_candidates,
        "count": len(ordered),
        "source_retrieved_at": snapshot["retrieved_at"],
        "source": snapshot["source"],
        "not_a_recommendation": True,
        "survivorship_warning": "Survivorship bias: this current universe snapshot must not be presented as a historically complete universe for past dates.",
        "rows": ordered,
    }


def _parse_history_rows(provider, payload, tx_symbol):
    if provider == "Tencent":
        return payload["data"][tx_symbol]["day"]
    return [x.split(",") for x in payload["data"]["klines"]]


def fetch_candidate_history(seed, start, end, request=request_json, *, max_symbols=60):
    """Fetch bounded raw daily history for candidate research.

    One request per candidate, Tencent first and Eastmoney fallback. No raw history
    needs to be committed to the repository.
    """
    date.fromisoformat(start)
    date.fromisoformat(end)
    if end < start or (date.fromisoformat(end) - date.fromisoformat(start)).days > 400:
        raise ValueError("invalid history interval")
    rows = seed.get("rows") or []
    if len(rows) > max_symbols:
        raise ValueError("candidate seed exceeds history budget")
    output, attempts, names = {}, [], {}
    for item in rows:
        symbol, name = item["symbol"], item["name"]
        code, exchange = symbol.split(".")
        if not _eligible(code, 1 if exchange == "SH" else 0):
            raise ValueError("unsupported candidate security")
        names[symbol] = name
        tx_symbol = exchange.lower() + code
        tx_url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urlencode({
            "param": f"{tx_symbol},day,{start},{end},320,"
        })
        em_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urlencode({
            "secid": f"{1 if exchange == 'SH' else 0}.{code}", "klt": 101, "fqt": 0,
            "beg": start.replace("-", ""), "end": end.replace("-", ""),
            "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57",
        })
        errors = []
        for provider, url in (("Tencent", tx_url), ("Eastmoney", em_url)):
            try:
                raw = _parse_history_rows(provider, request(url), tx_symbol)
                selected = {x[0]: {
                    "open": str(number(x[1])), "close": str(number(x[2])),
                    "high": str(number(x[3])), "low": str(number(x[4])),
                    "volume": str(number(x[5])) if len(x) > 5 and x[5] not in (None, "") else None,
                    "source": url, "provider": provider,
                } for x in raw if start <= x[0] <= end}
                if len(selected) < 2:
                    raise ValueError("insufficient returned sessions")
                output[symbol] = selected
                attempts.append({"symbol": symbol, "provider": provider, "status": "OK",
                                 "rows": len(selected), "fallback_errors": errors})
                break
            except Exception as exc:
                errors.append({"provider": provider, "error": f"{type(exc).__name__}: {exc}"[:400]})
        else:
            attempts.append({"symbol": symbol, "status": "FAILED", "errors": errors})
    good = [x for x in rows if x["symbol"] in output]
    if not good:
        return None, attempts

    sessions = sorted(set().union(*(set(x) for x in output.values())))
    tick = Decimal("0.01")
    for symbol, series in output.items():
        days = sorted(series)
        for i, day in enumerate(days):
            bar = series[day]
            bar["suspended"] = False
            if i == 0:
                bar["limit_up"] = None
                bar["limit_down"] = None
                continue
            prev = number(series[days[i-1]]["close"])
            cur = number(bar["close"])
            opened = number(bar["open"])
            if abs(cur / prev - 1) > Decimal("0.25") or abs(opened / prev - 1) > Decimal("0.25"):
                bar["limit_up"] = None
                bar["limit_down"] = None
                bar["limit_rule"] = "SUSPECTED_CORPORATE_ACTION_OR_DATA_BASIS_BREAK"
            else:
                bar["limit_up"] = str((prev * Decimal("1.10")).quantize(tick, rounding=ROUND_HALF_UP))
                bar["limit_down"] = str((prev * Decimal("0.90")).quantize(tick, rounding=ROUND_HALF_UP))
                bar["limit_rule"] = "ORDINARY_MAIN_BOARD_10PCT_FROM_PREVIOUS_CLOSE"

    dataset = {
        "schema_version": "0.4",
        "kind": "REAL_HISTORY",
        "price_basis": "unadjusted",
        "fidelity": "BOUNDED_CANDIDATE_REAL_DAILY",
        "sessions": sessions,
        "calendar_source": "union of returned candidate sessions; not independently certified",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Candidate set is bounded for compute control and is not a complete all-A-share research claim.",
            "No archived news/fundamentals/intraday verification in this adapter.",
            "Current-universe seeding has survivorship bias if reused for historical dates.",
            "Suspected >25% price-basis breaks are not assigned executable limit prices.",
        ],
        "instruments": {r["symbol"]: {
            "name": names[r["symbol"]], "board": "MAIN", "lot_size": 100,
            "price_limit_pct": "0.10",
        } for r in good},
        "bars": {d: {s: output[s][d] for s in output if d in output[s]} for d in sessions},
        "evidence": [],
        "corporate_actions": [],
    }
    validate_dataset(dataset)
    return dataset, attempts
