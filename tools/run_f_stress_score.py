#!/usr/bin/env python3
"""Causal F01 stress test: monitor after a large drop and compare with naive immediate bottom-fishing."""
from __future__ import annotations
import argparse,json,math
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
from stock_cn.simulation import Store,dumps,identifier,require
from stock_cn.universe import fetch_candidate_history, update_abnormal_drop_watchlist
from stock_cn.sim_data import number

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def ann(r,h): return (1+r)**(252/h)-1 if r>-1 else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",default=".")
    ap.add_argument("--request",required=True)
    args=ap.parse_args()
    repo=Path(args.repo).resolve()
    spec=load(repo/args.request); eval_id=identifier(spec["eval_id"])
    results=[]
    for ep in spec["episodes"]:
        symbol,name,target=ep["symbol"],ep["name"],ep["date"]
        start=(date.fromisoformat(target)-timedelta(days=40)).isoformat()
        end=(date.fromisoformat(target)+timedelta(days=120)).isoformat()
        seed={"kind":"BOUNDED_CANDIDATE_SEED","purpose":"ABNORMAL_DROP","count":1,
              "source":"fixed historical stress event","rows":[{
                "symbol":symbol,"name":name,"price_cny":str(ep["close"]),
                "change_pct":str(ep["change_pct"]),"amount_cny":None,
                "risk_tags":[],"source_provider":"historical stress probe"}]}
        data,attempts=fetch_candidate_history(seed,start,end,max_symbols=1)
        require(data is not None and target in data["sessions"],"episode history unavailable")
        idx=data["sessions"].index(target)
        watch=None; timeline=[]
        for j in range(idx,min(idx+spec.get("monitor_sessions",10),len(data["sessions"]))):
            day=data["sessions"][j]
            day_seed=seed if j==idx else {**seed,"count":0,"rows":[]}
            watch=update_abnormal_drop_watchlist(watch,day_seed,data,day,max_entries=10)
            item=watch["candidate_watchlist"][0]
            timeline.append({"date":day,"state":item["research_state"],
                             "evidence":item.get("recovery_evidence",[]),
                             "close":item.get("last_close_cny")})
        confirmation=next((x for x in timeline if x["state"]=="RECOVERY_CONFIRMATION_RESEARCH"),None)

        ex_idx=idx+1
        require(ex_idx < len(data["sessions"]),"no next session for naive baseline")
        ex_day=data["sessions"][ex_idx]; bar=data["bars"][ex_day][symbol]
        open_price=number(bar["open"])
        capital=Decimal(str(spec.get("capital_cny",200000)))
        pct=Decimal(str(spec.get("naive_position_pct",0.10)))
        qty=int(capital*pct/open_price/100)*100
        fee=Decimal("5.00") if qty else Decimal("0")
        cash=capital-open_price*qty-fee
        horizons=[]
        for h in spec.get("score_horizons",[5,20,40]):
            k=ex_idx+h
            if k>=len(data["sessions"]):
                horizons.append({"horizon_sessions":h,"status":"INSUFFICIENT_FUTURE_SESSIONS"}); continue
            day=data["sessions"][k]; close=number(data["bars"][day][symbol]["close"])
            equity=cash+close*qty
            ret=float(equity/capital-1)
            horizons.append({"horizon_sessions":h,"date":day,"naive_equity_cny":str(equity.quantize(Decimal("0.01"))),
                             "naive_return_pct":ret*100,
                             "F01_cash_return_pct":0.0,
                             "F01_advantage_vs_naive_pct":-ret*100,
                             "naive_annualized_pct":ann(ret,h)*100 if ann(ret,h) is not None else None})
        results.append({"symbol":symbol,"name":name,"drop_date":target,
                        "drop_change_pct":ep["change_pct"],"execution_baseline_date":ex_day,
                        "naive_quantity":qty,"timeline":timeline,
                        "recovery_confirmation":confirmation,
                        "F01_action_during_monitor":"HOLD/RESEARCH_ONLY until AI-confirmed recovery",
                        "horizons":horizons,"attempts":attempts})
    out={"eval_id":eval_id,"variant":"F01","method":"CAUSAL_WATCHLIST_VS_NAIVE_10PCT_NEXT_OPEN",
         "capital_cny":spec.get("capital_cny",200000),"results":results,
         "note":"Stress-test baseline only; F01 watchlist state is not itself an AI BUY signal.",
         "formal_execution":False}
    root=repo/"runs/evaluations"/eval_id
    Store(root).write("summary.json",out)
    rows=["|事件|F01回升确认|5日相对立即抄底|20日|40日|",
          "|---|---|---:|---:|---:|"]
    for x in results:
        m={y["horizon_sessions"]:y for y in x["horizons"]}
        def v(h):
            y=m.get(h,{})
            return "—" if y.get("status") else f"{y['F01_advantage_vs_naive_pct']:+.2f}%"
        conf=x["recovery_confirmation"]["date"] if x["recovery_confirmation"] else "观察期内无"
        rows.append(f"|{x['name']} {x['drop_date']}|{conf}|{v(5)}|{v(20)}|{v(40)}|")
    Store(root).write("summary.md","# F01异常下跌压力测试\n\n"+"\n".join(rows)+"\n")
    print(dumps(out))
if __name__=="__main__": main()
