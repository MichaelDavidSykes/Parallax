from __future__ import annotations

import json
import sys
from typing import Any, Dict, List


def generate(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    snapshots = payload.get("snapshots", [])
    cash = float(payload.get("cash") or 0)
    params = payload.get("parameters", {})
    min_edge = float(params.get("min_edge", 0.04))
    max_position_pct = float(params.get("max_position_pct", 0.08))
    signals: List[Dict[str, Any]] = []
    if cash <= 0:
        return signals
    for snapshot in snapshots if isinstance(snapshots, list) else []:
        yes_price = float(snapshot.get("yes_price") or 0.5)
        fair_probability = float(snapshot.get("fair_probability") or yes_price)
        edge = fair_probability - yes_price
        if abs(edge) < min_edge:
            continue
        side = "BUY_YES" if edge > 0 else "BUY_NO"
        price = yes_price if side == "BUY_YES" else 1 - yes_price
        stake = min(cash * max_position_pct, cash)
        signals.append(
            {
                "market_id": str(snapshot.get("market_id")),
                "side": side,
                "outcome": "YES" if side == "BUY_YES" else "NO",
                "price": price,
                "fair_probability": fair_probability,
                "edge": edge,
                "confidence": float(snapshot.get("confidence") or 0.5),
                "quantity": stake / max(price, 0.01),
                "timestamp": str(snapshot.get("captured_at")),
                "rationale": "Container model probability edge.",
            }
        )
    return signals


def main() -> None:
    payload = json.load(sys.stdin)
    json.dump({"signals": generate(payload)}, sys.stdout)


if __name__ == "__main__":
    main()
