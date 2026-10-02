#!/usr/bin/env python3
"""Bounded real-source probe for official disclosure metadata.

The probe writes compact CNINFO metadata only. It does not download PDFs, extract
financial conclusions, invoke a paid model, or change any strategy/account file.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from stock_cn.evidence import build_official_disclosure_pack
from stock_cn.simulation import Store, dumps, identifier


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--probe-id", required=True)
    p.add_argument("--symbols", nargs="+", required=True)
    p.add_argument("--lookback-days", type=int, default=120)
    p.add_argument("--max-pages", type=int, default=3)
    args = p.parse_args()
    identifier(args.probe_id)
    if not 7 <= args.lookback_days <= 365:
        raise ValueError("lookback-days must be 7..365")
    if not 1 <= args.max_pages <= 6:
        raise ValueError("max-pages must be 1..6")

    repo = Path(args.repo).resolve()
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    end = now.date()
    start = end - timedelta(days=args.lookback_days)
    pack = build_official_disclosure_pack(
        args.symbols,
        start.isoformat(),
        end.isoformat(),
        as_of=now.isoformat(),
        max_pages_per_symbol=args.max_pages,
    )
    statuses = {r["symbol"]: r["provider_status"] for r in pack["results"]}
    summary = {
        "probe_id": args.probe_id,
        "provider": pack["provider"],
        "provider_official": pack["provider_official"],
        "as_of": pack["as_of"],
        "requested_start": pack["requested_start"],
        "requested_end": pack["requested_end"],
        "symbols": args.symbols,
        "statuses": statuses,
        "verified_for_all_symbols": pack["complete_for_requested_symbols"],
        "announcement_count": sum(len(r.get("items", [])) for r in pack["results"]),
        "periodic_report_ref_count": len(pack["latest_periodic_report_refs"]),
        "important_ref_count": len(pack["important_recent_refs"]),
        "metadata_only": True,
        "pdf_downloaded": False,
        "financial_conclusions_extracted": False,
        "formal_execution": False,
    }
    root = repo / "runs/research/evidence" / args.probe_id
    store = Store(root)
    store.write("summary.json", summary)
    store.write("official-disclosure-pack.json", pack)
    store.write(
        "summary.md",
        "# 官方披露源探测\n\n"
        "本结果仅验证公告元数据读取，不是投资判断，也未解析PDF全文。\n\n"
        + dumps(summary)
    )
    print(dumps(summary))


if __name__ == "__main__":
    main()
