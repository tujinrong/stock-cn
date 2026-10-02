"""AI adapters. ScriptedSmokeAgent is TEST ONLY, never the investment strategy."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from urllib.request import Request, urlopen

from .simulation import ValidationError, require


class Budget:
    def __init__(self, max_calls=100, max_input_chars=80000, max_output_tokens=2500):
        require(isinstance(max_calls, int) and 0 < max_calls <= 1000, "invalid call budget")
        self.maximum = max_calls
        self.max_input_chars = max_input_chars
        self.max_output_tokens = max_output_tokens
        self.calls = 0
        self.lock = threading.Lock()

    def claim(self, prompt):
        with self.lock:
            require(len(prompt) <= self.max_input_chars, "input budget exceeded; do not silently drop holdings/rules")
            require(self.calls < self.maximum, "batch call budget exhausted")
            self.calls += 1


def decision_base(request):
    c = request["context"]
    result = {k: c[k] for k in ("strategy_id", "variant_id", "mode", "run_id", "decision_id", "date", "decision_time", "input_revision", "input_commit")}
    result.update(schema_version="0.3-draft", status="READY", action="HOLD", order_proposal=None,
                  target_weights=None, target_cash_weight=None, summary="", risks=[], evidence=[], data_gaps=[])
    return result


class ScriptedSmokeAgent:
    """Deterministic exercise of BUY/SELL/HOLD plumbing; NO AI or stock recommendation."""
    def __init__(self, budget=None, demonstrate_repair=False):
        self.budget = budget or Budget()
        self.demonstrate_repair = demonstrate_repair
        self.first = True

    def decide(self, request, errors):
        self.budget.claim(request["prompt"])
        require(request["context"]["fidelity"] in {"ENGINEERING_ONLY", "FLOW_ONLY_REAL_PRICES"}, "scripted agent prohibited for investment validation")
        if self.first and self.demonstrate_repair:
            self.first = False
            return {"status": "READY", "action": "BUY"}  # Intentional schema fault, never a trade.
        self.first = False
        day_number = int(request["context"]["date"][-2:])
        action = {4: "BUY", 5: "SELL", 6: "HOLD", 7: "BUY", 8: "SELL"}.get(day_number, "HOLD")
        response = decision_base(request)
        response.update(action=action, summary="TEST_ONLY：脚本用于验证AI接口、交易校验和记账，不是投资判断。",
                        risks=["不能用本次收益评价AI投资能力。"], data_gaps=["没有完整历史财务和新闻研究。"])
        if action != "HOLD":
            symbol = next(iter(request["market"]))
            bar = request["market"][symbol][-1]
            response["order_proposal"] = {"symbol": symbol, "side": action, "quantity": 100,
                                          "reference_price_cny": bar["close"],
                                          "quote_time": request["context"]["information_cutoff"], "quote_source": bar["source"]}
        return response


class FileAgent:
    """ChatGPT/manual bridge: write the full AI reply to <answers>/<variant>/<date>.json."""
    def __init__(self, folder, budget=None):
        self.folder, self.budget = Path(folder).resolve(), budget or Budget()

    def decide(self, request, errors):
        self.budget.claim(request["prompt"])
        c = request["context"]
        path = self.folder / c["variant_id"] / (c["date"] + ".json")
        require(path.is_file(), f"WAITING_FOR_AI: open requests/{c['date']}/ai_input.md, save reply to {path}")
        return path.read_text(encoding="utf-8")


class OpenAIResponsesAgent:
    """Optional paid API, disabled unless explicitly authorized. No web tools in replay.

    No default model, no API key in repository. A timeout is not blindly retried.
    The supplied historical evidence is the only external context sent to the model.
    """
    def __init__(self, model, *, allow_paid=False, budget=None):
        require(allow_paid and model, "explicit --allow-paid and --model required")
        self.key = os.environ.get("OPENAI_API_KEY")
        require(bool(self.key), "OPENAI_API_KEY not configured")
        self.model, self.budget = model, budget or Budget(max_calls=10)

    def decide(self, request, errors):
        self.budget.claim(request["prompt"])
        payload = {"model": self.model, "input": request["prompt"],
                   "instructions": "Use only supplied point-in-time evidence. Return one JSON object; do not claim unperformed research.",
                   "max_output_tokens": self.budget.max_output_tokens, "store": False}
        call = Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode(),
                       headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}, method="POST")
        with urlopen(call, timeout=90) as reply:
            body = json.loads(reply.read(2_000_000))
        require(body.get("status") == "completed", "model response incomplete; no trade")
        text = "".join(c.get("text", "") for item in body.get("output", []) if item.get("type") == "message"
                       for c in item.get("content", []) if c.get("type") == "output_text").strip()
        if text.startswith("```json") and text.endswith("```"):
            text = text[7:-3].strip()
        return text
