from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


@dataclass
class StrategySignal:
    market_id: str
    side: str
    outcome: str
    price: float
    fair_probability: float
    edge: float
    confidence: float
    quantity: float
    timestamp: str
    rationale: str


class Strategy(Protocol):
    name: str

    def generate(self, snapshots: List[Dict[str, Any]], cash: float) -> List[StrategySignal]:
        ...


def implied_outcome(side: str) -> str:
    return "YES" if side == "BUY_YES" else "NO"

