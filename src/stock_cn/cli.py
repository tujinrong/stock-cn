from __future__ import annotations

import argparse

from .account import Account
from .ai import RuleBasedAIAnalyst
from .broker import PaperBroker
from .market import DemoMarketData
from .simulator import Simulator
from .strategy import MovingAverageCrossStrategy


def run_demo(symbol: str, initial_cash: float) -> None:
    market = DemoMarketData(days=80)
    bars = market.bars(symbol)

    account = Account(cash=initial_cash)
    broker = PaperBroker(account)
    strategy = MovingAverageCrossStrategy(symbol=symbol)
    analyst = RuleBasedAIAnalyst()
    result = Simulator(account, broker, strategy, analyst).run(bars)

    print(f"symbol       : {symbol}")
    print(f"initial cash : {result.initial_cash:,.2f}")
    print(f"final equity : {result.final_equity:,.2f}")
    print(f"return       : {result.return_pct:.2f}%")
    print(f"fills        : {result.fills}")
    if result.last_ai_view:
        print(f"AI score     : {result.last_ai_view.score:+.3f}")
        print(f"AI summary   : {result.last_ai_view.summary}")


def main() -> None:
    parser = argparse.ArgumentParser(description="A-share AI paper-trading simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run the offline demo")
    demo.add_argument("--symbol", default="600036.SH")
    demo.add_argument("--cash", type=float, default=1_000_000)

    args = parser.parse_args()
    if args.command == "demo":
        run_demo(args.symbol, args.cash)


if __name__ == "__main__":
    main()
