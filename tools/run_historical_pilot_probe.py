#!/usr/bin/env python3
"""Probe a predeclared historical pilot universe without outcome-based selection."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from stock_cn.simulation import Store, dumps, identifier, require
from stock_cn.time_travel import symbol_snapshot
from stock_cn.universe import fetch_candidate_history

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",default=".")
    ap.add_argument("--request",required=True)
    args=ap.parse_args()
    repo=Path(args.repo).resolve()
    spec=load(repo/args.request)
    probe_id=identifier(spec["probe_id"])
    rows=[{"symbol":x["symbol"],"name":x["name"],"risk_tags":[]} for x in spec["universe"]]
    seed={"kind":"BOUNDED_CANDIDATE_SEED","purpose":"HISTORICAL_PILOT_FIXED_UNIVERSE",
          "count":len(rows),"rows":rows,"source":"predeclared fixed pilot universe",
          "survivorship_warning":"Pilot universe is fixed ex ante for this experiment; not a claim of full historical A-share coverage."}
    data,attempts=fetch_candidate_history(seed,spec["history_start"],spec["history_end"],max_symbols=len(rows))
    require(data is not None,"historical pilot data unavailable")
    out={"probe_id":probe_id,"universe":spec["universe"],"target_dates":spec["target_dates"],
         "attempts":attempts,"snapshots":{},"raw_market_data_persisted":False}
    for day in spec["target_dates"]:
        require(day in data["sessions"],f"target date missing: {day}")
        out["snapshots"][day]=[
            symbol_snapshot(data,s,day) for s in data["instruments"]
            if symbol_snapshot(data,s,day) is not None
        ]
    Store(repo/"runs/research/historical-pilot"/probe_id).write("summary.json",out)
    print(dumps(out))
if __name__=="__main__":
    main()
