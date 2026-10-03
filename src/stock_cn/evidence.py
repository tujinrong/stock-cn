"""Official-disclosure evidence layer for AI investment research.

The code intentionally stores compact announcement metadata, not raw PDFs. Official
disclosures are facts/provenance inputs; title classification only routes research
attention and never implies bullish/bearish meaning.

CNINFO endpoints are public web interfaces rather than a guaranteed stable API.
Provider failure, a genuinely empty result, and filtered future evidence are always
reported separately so the AI cannot turn "fetch failed" into "no risk found".
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
from zoneinfo import ZoneInfo

CNINFO_ORIGIN = "https://www.cninfo.com.cn"
CNINFO_SEARCH_PAGE = (
    "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?"
    "url=disclosure/list/search"
)
CNINFO_TOP_SEARCH = "https://www.cninfo.com.cn/new/information/topSearch/query"
CNINFO_ANNOUNCEMENTS = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_STATIC = "https://static.cninfo.com.cn/"
BEIJING = ZoneInfo("Asia/Shanghai")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36"
)


class EvidenceProviderError(RuntimeError):
    pass


def _symbol_parts(symbol):
    if not isinstance(symbol, str) or not re.fullmatch(r"\d{6}\.(SH|SZ)", symbol):
        raise ValueError("unsupported A-share symbol")
    code, suffix = symbol.split(".")
    if suffix == "SH":
        if not code.startswith(("600", "601", "603", "605")):
            raise ValueError("unsupported/excluded Shanghai security")
        return code, "sse", "sh"
    if not code.startswith(("000", "001", "002", "003")):
        raise ValueError("unsupported/excluded Shenzhen security")
    return code, "szse", "sz"


def _headers():
    return {
        "User-Agent": UA,
        "Referer": CNINFO_SEARCH_PAGE,
        "Origin": CNINFO_ORIGIN,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }


@dataclass
class CninfoHttp:
    timeout: float = 20.0
    max_bytes: int = 5_000_000

    def __post_init__(self):
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))
        self._warmed = False

    def warm(self):
        if self._warmed:
            return
        req = Request(CNINFO_SEARCH_PAGE, headers={"User-Agent": UA})
        with self.opener.open(req, timeout=self.timeout) as response:
            response.read(200_000)
        self._warmed = True

    def post_json(self, url, form):
        self.warm()
        body = urlencode({k: "" if v is None else str(v) for k, v in form.items()}).encode("utf-8")
        req = Request(url, data=body, headers=_headers(), method="POST")
        with self.opener.open(req, timeout=self.timeout) as response:
            raw = response.read(self.max_bytes + 1)
        if len(raw) > self.max_bytes:
            raise EvidenceProviderError("CNINFO response exceeds bounded size")
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise EvidenceProviderError("CNINFO returned non-JSON response") from exc


def _clean_title(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"</?em[^>]*>", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _epoch_ms_to_iso(value):
    if value in (None, ""):
        return None
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceProviderError("invalid CNINFO announcementTime") from exc
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).astimezone(BEIJING).isoformat()


def _pdf_url(path):
    if not path:
        return None
    path = str(path).strip()
    if path.startswith("http://") or path.startswith("https://"):
        return path.replace("http://static.cninfo.com.cn/", CNINFO_STATIC)
    return CNINFO_STATIC + path.lstrip("/")


def classify_announcement_title(title):
    """Research-routing class only; no positive/negative conclusion."""
    t = _clean_title(title)
    rules = [
        ("PERIODIC_REPORT", ("年度报告", "半年度报告", "第一季度报告", "第三季度报告", "季度报告")),
        ("EARNINGS", ("业绩预告", "业绩快报", "盈利预测", "业绩说明会")),
        ("DIVIDEND", ("利润分配", "分红", "派息", "权益分派", "股息分派", "股息派发", "股利分配")),
        ("BUYBACK", ("回购",)),
        ("HOLDER_CHANGE", ("减持", "增持", "持股变动", "股东变动")),
        ("CONTRACT", ("重大合同", "中标", "订单", "项目合同")),
        ("MNA", ("重大资产重组", "收购", "出售资产", "吸收合并", "并购")),
        ("FINANCING", ("定向增发", "非公开发行", "向特定对象发行", "可转债", "配股", "融资")),
        ("GOVERNANCE", ("董事", "监事", "高级管理人员", "总经理", "董事会秘书", "辞职", "聘任")),
        ("RISK", ("立案", "处罚", "诉讼", "仲裁", "风险提示", "退市", "违规", "监管措施")),
    ]
    for category, words in rules:
        if any(x in t for x in words):
            return category
    return "OTHER"


def is_periodic_report_body(title):
    t = _clean_title(title)
    if any(x in t for x in (
        "摘要", "审计报告", "内部控制", "提示性公告", "英文", "译本",
        "修订说明", "修订内容", "修订部分", "更正说明", "更正内容", "更正部分",
        "更正公告", "补充公告",
    )):
        return False
    # Official issuers use both 2025年度报告 and 2025年年度报告, and may
    # omit 第 in 一季度/三季度. A corrected full report remains a body;
    # explanations, abstracts and translated excerpts do not become one.
    return bool(re.search(
        r"\d{4}(?:年)?(?:年度|半年度|第?[一三]季度)报告(?:（[^）]+）|\([^()]+\))?$", t))


def _extract_org_id(item, sec_code):
    if not isinstance(item, dict):
        return None
    for key in ("orgId", "orgID", "orgid"):
        value = item.get(key)
        if value:
            return str(value)

    # Current topSearch responses may use "code" for orgId and "key"/"secCode"
    # for the stock code.
    code_value = str(item.get("code") or "")
    if code_value and code_value != sec_code:
        if code_value.startswith(("gssh", "gssz", "gsbj")) or len(code_value) > 6:
            return code_value

    for key in ("data", "stock", "result"):
        nested = item.get(key)
        if isinstance(nested, dict):
            found = _extract_org_id(nested, sec_code)
            if found:
                return found
    return None


def resolve_cninfo_org_id(symbol, post_json):
    code, _, _ = _symbol_parts(symbol)
    payload = post_json(CNINFO_TOP_SEARCH, {"keyWord": code, "maxNum": 10})
    if isinstance(payload, dict):
        for key in ("stockList", "data", "result", "records"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise EvidenceProviderError("unexpected CNINFO topSearch response")

    ordered = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        fields = [str(item.get(k) or "") for k in ("key", "secCode", "stockCode")]
        if code in fields or any(code in x for x in fields):
            ordered.insert(0, item)
        else:
            ordered.append(item)
    for item in ordered:
        org_id = _extract_org_id(item, code)
        if org_id:
            return org_id
    raise EvidenceProviderError(f"CNINFO orgId not resolved for {symbol}")


def _normalize_announcement(symbol, raw, retrieved_at):
    title = _clean_title(raw.get("announcementTitle") or raw.get("title"))
    published_at = _epoch_ms_to_iso(raw.get("announcementTime"))
    if not title or not published_at:
        raise EvidenceProviderError("CNINFO announcement missing title/time")
    return {
        "symbol": symbol,
        "sec_name": raw.get("secName"),
        "announcement_id": str(raw.get("announcementId") or raw.get("id") or ""),
        "title": title,
        "category": classify_announcement_title(title),
        "is_periodic_report_body": is_periodic_report_body(title),
        "published_at": published_at,
        "retrieved_at": retrieved_at,
        "source_provider": "CNINFO",
        "source_official": True,
        "source": CNINFO_ORIGIN,
        "document_url": _pdf_url(raw.get("adjunctUrl")),
        "document_format": "PDF" if raw.get("adjunctUrl") else None,
        "metadata_only": True,
        "research_meaning": "OFFICIAL_DISCLOSURE_REFERENCE_NOT_FINANCIAL_CONCLUSION",
    }


def fetch_cninfo_announcements(
    symbol,
    start_date,
    end_date,
    *,
    as_of=None,
    max_pages=4,
    post_json=None,
):
    """Fetch bounded official announcement metadata for one stock."""
    code, column, plate = _symbol_parts(symbol)
    date.fromisoformat(start_date)
    date.fromisoformat(end_date)
    if end_date < start_date:
        raise ValueError("invalid evidence date range")
    if type(max_pages) is not int or not 1 <= max_pages <= 10:
        raise ValueError("announcement page budget must be 1..10")

    client = CninfoHttp()
    post = post_json or client.post_json
    org_id = resolve_cninfo_org_id(symbol, post)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    as_of_dt = datetime.fromisoformat(as_of) if as_of else None
    if as_of_dt is not None and as_of_dt.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")

    items = []
    provider_rows = 0
    future_filtered = 0
    pages_used = 0
    for page in range(1, max_pages + 1):
        payload = post(CNINFO_ANNOUNCEMENTS, {
            "stock": f"{code},{org_id}",
            "tabName": "fulltext",
            "pageSize": 30,
            "pageNum": page,
            "column": column,
            "category": "",
            "plate": plate,
            "searchkey": "",
            "secid": "",
            "trade": "",
            "seDate": f"{start_date}~{end_date}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        })
        if not isinstance(payload, dict):
            raise EvidenceProviderError("unexpected CNINFO announcement response")
        rows = payload.get("announcements") or []
        if not isinstance(rows, list):
            raise EvidenceProviderError("CNINFO announcements is not a list")
        pages_used += 1
        provider_rows += len(rows)
        for raw in rows:
            item = _normalize_announcement(symbol, raw, retrieved_at)
            published = datetime.fromisoformat(item["published_at"])
            if as_of_dt is not None and published > as_of_dt:
                future_filtered += 1
                continue
            items.append(item)
        if not rows or not payload.get("hasMore"):
            break

    dedup = {}
    for item in items:
        day = item["published_at"][:10]
        key = (item["symbol"], day, item["title"])
        if key not in dedup or (not dedup[key].get("document_url") and item.get("document_url")):
            dedup[key] = item
    items = sorted(dedup.values(), key=lambda x: x["published_at"], reverse=True)
    return {
        "symbol": symbol,
        "provider": "CNINFO",
        "provider_official": True,
        "provider_status": "OK" if items else "EMPTY",
        "org_id": org_id,
        "column": column,
        "plate": plate,
        "requested_start": start_date,
        "requested_end": end_date,
        "as_of": as_of,
        "pages_used": pages_used,
        "provider_rows": provider_rows,
        "items": items,
        "future_items_filtered": future_filtered,
    }


def build_official_disclosure_pack(
    symbols,
    start_date,
    end_date,
    *,
    as_of=None,
    max_pages_per_symbol=4,
    post_json=None,
):
    if not symbols or len(symbols) > 20:
        raise ValueError("official disclosure pack requires 1..20 symbols")
    results = []
    for symbol in symbols:
        try:
            result = fetch_cninfo_announcements(
                symbol, start_date, end_date, as_of=as_of,
                max_pages=max_pages_per_symbol, post_json=post_json,
            )
        except Exception as exc:
            result = {
                "symbol": symbol,
                "provider": "CNINFO",
                "provider_official": True,
                "provider_status": "FAILED",
                "items": [],
                "error": f"{type(exc).__name__}: {exc}"[:800],
            }
        results.append(result)

    all_items = [x for r in results for x in r.get("items", [])]
    periodic = [x for x in all_items if x.get("is_periodic_report_body")]
    important = [x for x in all_items if x.get("category") in {
        "EARNINGS", "BUYBACK", "HOLDER_CHANGE", "CONTRACT", "MNA",
        "FINANCING", "GOVERNANCE", "RISK", "DIVIDEND",
    }]
    failures = [r for r in results if r.get("provider_status") == "FAILED"]
    return {
        "kind": "OFFICIAL_DISCLOSURE_PACK",
        "provider": "CNINFO",
        "provider_official": True,
        "requested_start": start_date,
        "requested_end": end_date,
        "as_of": as_of,
        "symbols_requested": list(symbols),
        "symbols_ok_or_empty": [
            r["symbol"] for r in results if r.get("provider_status") in {"OK", "EMPTY"}
        ],
        "symbols_failed": [r["symbol"] for r in failures],
        "complete_for_requested_symbols": not failures,
        "results": results,
        "latest_periodic_report_refs": sorted(
            periodic, key=lambda x: x["published_at"], reverse=True
        )[:len(symbols) * 3],
        "important_recent_refs": sorted(
            important, key=lambda x: x["published_at"], reverse=True
        )[:50],
        "metadata_only": True,
        "financial_conclusions_extracted": False,
        "news_research_required": True,
        "news_policy": (
            "Recent media/news may be searched by the AI when relevant, but material "
            "facts must be rechecked against official disclosure when possible."
        ),
        "failure_semantics": (
            "FAILED means source/query failure and must never be interpreted as "
            "'no announcements' or 'no risk'. EMPTY means the provider responded "
            "successfully but returned no items in the bounded query."
        ),
    }



def validate_official_disclosure_pack(pack, *, as_of, required_symbols=None):
    """Validate causal official-disclosure metadata for a decision-time snapshot."""
    if not isinstance(pack, dict) or pack.get("kind") != "OFFICIAL_DISCLOSURE_PACK":
        raise ValueError("official disclosure pack missing or invalid")
    cutoff = datetime.fromisoformat(as_of)
    if cutoff.tzinfo is None:
        raise ValueError("official disclosure cutoff must be timezone-aware")
    results = pack.get("results")
    if not isinstance(results, list):
        raise ValueError("official disclosure results missing")
    by_symbol = {}
    for result in results:
        symbol = result.get("symbol")
        if not symbol:
            raise ValueError("official disclosure result missing symbol")
        status = result.get("provider_status")
        if status not in {"OK", "EMPTY", "FAILED"}:
            raise ValueError("invalid official disclosure provider status")
        by_symbol[symbol] = result
        for item in result.get("items", []):
            published = datetime.fromisoformat(item["published_at"])
            if published.tzinfo is None or published > cutoff:
                raise ValueError("future/naive official disclosure in decision pack")
            if item.get('publication_precision', '').startswith('DATE_ONLY') and published.astimezone(cutoff.tzinfo).date() >= cutoff.date():
                raise ValueError('date-only official disclosure unavailable at intraday cutoff')
            if item.get("source_official") is not True:
                raise ValueError("non-official item inside official disclosure pack")
    required = set(required_symbols or [])
    missing = sorted(required - set(by_symbol))
    if missing:
        raise ValueError("official disclosure coverage missing symbols: " + ",".join(missing))
    return True


def official_disclosure_status(pack, symbol):
    if not isinstance(pack, dict):
        return "NOT_CHECKED"
    for result in pack.get("results", []):
        if result.get("symbol") == symbol:
            return result.get("provider_status") or "INVALID"
    return "NOT_CHECKED"
