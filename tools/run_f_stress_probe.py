#!/usr/bin/env python3
"""Find stress-test abnormal-drop episodes inside a predeclared pilot universe."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from stock_cn.simulation import Store, dumps, identifier, require
from stock_cn.universe import fetch_candidate_history

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",default=".")
    ap.add_argument("--request",required=True)
    args=ap.parse_args()
    repo=Path(args.repo).resolve()
    spec=load(repo/args.request)
    probe_id=identifier(spec["probe_id"])
    rows=[{"symbol":x["symbol"],"name":x["name"],"risk_tags":[]} for x in spec["universe"]]
    seed={"kind":"BOUNDED_CANDIDATE_SEED","purpose":"F_STRESS_EVENT_DISCOVERY",
          "count":len(rows),"rows":rows,"source":"predeclared fixed pilot universe",
          "survivorship_warning":"Stress-test discovery only; not full-market coverage."}
    data,attempts=fetch_candidate_history(seed,spec["history_start"],spec["history_end"],max_symbols=len(rows))
    require(data is not None,"history unavailable")
    episodes=[]
    for symbol in data["instruments"]:
        prev=None
        for day in data["sessions"]:
            bar=data["bars"].get(day,{}).get(symbol)
            if not bar: continue
            close=float(bar["close"])
            if prev is not None:
                chg=(close/prev-1)*100
                if chg <= spec.get("drop_threshold_pct",-5):
                    episodes.append({
                        "symbol":symbol,"name":data["instruments"][symbol]["name"],
                        "date":day,"close":close,"previous_close":prev,
                        "change_pct":chg
                    })
            prev=close
    episodes.sort(key=lambda x:x["change_pct"])
    out={"probe_id":probe_id,"threshold_pct":spec.get("drop_threshold_pct",-5),
         "episodes":episodes[:spec.get("max_events",20)],"attempts":attempts,
         "selection_note":"Used only to choose F stress-test episodes; not a trading rule.",
         "raw_market_data_persisted":False}
    Store(repo/"runs/research/historical-pilot"/probe_id).write("summary.json",out)
    print(dumps(out))
if __name__=="__main__": main()
