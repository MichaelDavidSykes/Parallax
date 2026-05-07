from __future__ import annotations

from typing import Any, Dict, List

from backend.strategies.base import StrategySignal


class StatArbStrategy:
    name = "stat_arb_v1"

    def __init__(
        self,
        min_edge: float = 0.04,
        max_position_pct: float = 0.08,
        fee_bps: float = 0,
    ):
        self.min_edge = min_edge
        self.max_position_pct = max_position_pct
        self.fee_bps = fee_bps

    def generate(self, snapshots: List[Dict[str, Any]], cash: float) -> List[StrategySignal]:
        signals: List[StrategySignal] = []
        if cash <= 0:
            return signals
        for snapshot in snapshots:
            yes_price = float(snapshot["yes_price"])
            fair_probability = float(snapshot["fair_probability"])
            confidence = float(snapshot.get("confidence", 0.5))
            edge = fair_probability - yes_price
            fee_drag = self.fee_bps / 10000
            net_edge = abs(edge) - fee_drag
            if net_edge < self.min_edge:
                continue
            side = "BUY_YES" if edge > 0 else "BUY_NO"
            price = yes_price if side == "BUY_YES" else float(snapshot["no_price"])
            stake = min(cash * self.max_position_pct, cash)
            quantity = stake / max(price, 0.01)
            signals.append(
                StrategySignal(
                    market_id=str(snapshot["market_id"]),
                    side=side,
                    outcome="YES" if side == "BUY_YES" else "NO",
                    price=price,
                    fair_probability=fair_probability,
                    edge=edge,
                    confidence=confidence,
                    quantity=quantity,
                    timestamp=str(snapshot["captured_at"]),
                    rationale="Fair probability diverged from Polymarket price after fee drag.",
                )
            )
        return signals

