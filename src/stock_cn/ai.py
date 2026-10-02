from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .domain import Bar


@dataclass(frozen=True)
class AIView:
    score: float
    summary: str
    confidence: float


class AIAnalyst(Protocol):
    def analyze(self, symbol: str, history: list[Bar]) -> AIView:
        ...


class RuleBasedAIAnalyst:
    """Offline placeholder implementing the same interface as a future LLM analyst."""

    def analyze(self, symbol: str, history: list[Bar]) -> AIView:
        if len(history) < 20:
            return AIView(0.0, "历史数据不足", 0.2)

        recent = history[-20:]
        first = recent[0].close
        last = recent[-1].close
        momentum = (last / first) - 1
        score = max(-1.0, min(1.0, momentum * 8))
        direction = "偏强" if score > 0.15 else ("偏弱" if score < -0.15 else "中性")
        return AIView(
            score=round(score, 3),
            summary=f"{symbol} 近20个交易日走势{direction}，规则模型动量={momentum:.2%}",
            confidence=0.55,
        )
