from __future__ import annotations

from dataclasses import dataclass

from .account import Account
from .ai import AIAnalyst, AIView
from .broker import PaperBroker
from .domain import Bar
from .strategy import Strategy


@dataclass
class SimulationResult:
    initial_cash: float
    final_equity: float
    fills: int
    return_pct: float
    last_ai_view: AIView | None


class Simulator:
    def __init__(
        self,
        account: Account,
        broker: PaperBroker,
        strategy: Strategy,
        ai_analyst: AIAnalyst | None = None,
    ) -> None:
        self.account = account
        self.broker = broker
        self.strategy = strategy
        self.ai_analyst = ai_analyst

    def run(self, bars: list[Bar]) -> SimulationResult:
        if not bars:
            raise ValueError("bars cannot be empty")

        initial_cash = self.account.cash
        history: list[Bar] = []
        current_date = None
        last_ai_view = None

        for bar in bars:
            if current_date != bar.trading_date:
                self.account.begin_day(bar.trading_date)
                current_date = bar.trading_date

            history.append(bar)
            self.account.mark(bar.symbol, bar.close)
            position_qty = self.account.position(bar.symbol).quantity

            for order in self.strategy.on_bar(history, position_qty):
                try:
                    self.broker.execute(order, bar)
                except ValueError:
                    pass

            if self.ai_analyst is not None:
                last_ai_view = self.ai_analyst.analyze(bar.symbol, history)

        final_equity = self.account.total_equity
        return SimulationResult(
            initial_cash=initial_cash,
            final_equity=final_equity,
            fills=len(self.account.fills),
            return_pct=(final_equity / initial_cash - 1) * 100,
            last_ai_view=last_ai_view,
        )
