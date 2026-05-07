from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from backend.db.database import Database, utc_now
from backend.services.model_registry_service import ModelRegistryService
from backend.services.opportunity_service import OpportunityService
from backend.strategies.stat_arb import StatArbStrategy


class BacktestService:
    def __init__(self, db: Database):
        self.db = db
        self.opportunity_service = OpportunityService(db)

    async def run(
        self,
        name: str,
        strategy: str,
        model_id: str,
        initial_cash: float,
        market_limit: int,
        min_edge: float,
        max_position_pct: float,
        fee_bps: float,
        slippage_bps: float,
        valuation_basis: str,
        refresh_markets: bool = True,
    ) -> Dict[str, Any]:
        started_at = utc_now()
        if refresh_markets:
            await self.opportunity_service.scan(
                market_limit=market_limit,
                min_edge=min_edge,
                refresh_markets=True,
            )

        snapshots = self.db.list_snapshots(limit=max(500, market_limit * 30))
        snapshots = snapshots[-max(1, market_limit * 30):]
        grouped = self._group_by_time(snapshots)
        model = ModelRegistryService().get(model_id or strategy)
        selected_strategy = self._strategy_for(
            strategy=str(model.get("strategy") or strategy),
            min_edge=min_edge,
            max_position_pct=max_position_pct,
            fee_bps=fee_bps,
        )

        cash = initial_cash
        positions: Dict[Tuple[str, str], Dict[str, Any]] = {}
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []
        latest_marks: Dict[str, Dict[str, Any]] = {}

        for captured_at, bucket in grouped:
            for snapshot in bucket:
                latest_marks[str(snapshot["market_id"])] = snapshot
            signals = selected_strategy.generate(bucket, cash)
            for signal in signals:
                execution_price = self._execution_price(signal.price, signal.side, slippage_bps)
                notional = signal.quantity * execution_price
                fees = notional * (fee_bps / 10000)
                if notional + fees > cash:
                    continue
                cash -= notional + fees
                key = (signal.market_id, signal.outcome)
                position = positions.setdefault(
                    key,
                    {
                        "market_id": signal.market_id,
                        "outcome": signal.outcome,
                        "quantity": 0.0,
                        "cost": 0.0,
                    },
                )
                position["quantity"] += signal.quantity
                position["cost"] += notional + fees
                trades.append(
                    {
                        "timestamp": signal.timestamp,
                        "market_id": signal.market_id,
                        "side": signal.side,
                        "outcome": signal.outcome,
                        "quantity": signal.quantity,
                        "price": execution_price,
                        "raw_signal_price": signal.price,
                        "notional": notional,
                        "fees": fees,
                        "edge": signal.edge,
                        "confidence": signal.confidence,
                        "rationale": signal.rationale,
                    }
                )
            equity_curve.append(
                {
                    "timestamp": captured_at,
                    "cash": cash,
                    "equity": self._mark_equity(cash, positions, latest_marks, valuation_basis),
                }
            )

        final_equity = self._mark_equity(cash, positions, latest_marks, valuation_basis)
        completed_at = utc_now()
        avg_edge = (
            sum(abs(float(trade["edge"])) for trade in trades) / len(trades)
            if trades
            else 0
        )
        run = {
            "id": str(uuid4()),
            "name": name,
            "strategy": selected_strategy.name,
            "model_id": model["id"],
            "initial_cash": initial_cash,
            "final_equity": final_equity,
            "return_pct": ((final_equity - initial_cash) / initial_cash) * 100,
            "started_at": started_at,
            "completed_at": completed_at,
            "parameters": {
                "market_limit": market_limit,
                "min_edge": min_edge,
                "max_position_pct": max_position_pct,
                "fee_bps": fee_bps,
                "slippage_bps": slippage_bps,
                "valuation_basis": valuation_basis,
                "refresh_markets": refresh_markets,
                "model_runtime": model.get("runtime"),
                "model_image": model.get("image"),
            },
            "metrics": {
                "snapshots": len(snapshots),
                "trade_count": len(trades),
                "avg_abs_edge": avg_edge,
                "open_positions": len(positions),
                "cash": cash,
            },
            "equity_curve": equity_curve,
            "trades": trades,
        }
        self.db.save_backtest(run)
        return run

    def list(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.db.list_backtests(limit=limit)

    def _strategy_for(
        self,
        strategy: str,
        min_edge: float,
        max_position_pct: float,
        fee_bps: float,
    ) -> StatArbStrategy:
        if strategy != "stat_arb_v1":
            raise ValueError(
                "Unknown strategy. Add a strategy class under backend/strategies and register it here."
            )
        return StatArbStrategy(
            min_edge=min_edge,
            max_position_pct=max_position_pct,
            fee_bps=fee_bps,
        )

    def _group_by_time(self, snapshots: List[Dict[str, Any]]) -> List[Tuple[str, List[Dict[str, Any]]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for snapshot in snapshots:
            grouped[str(snapshot["captured_at"])].append(snapshot)
        return sorted(grouped.items(), key=lambda item: item[0])

    def _mark_equity(
        self,
        cash: float,
        positions: Dict[Tuple[str, str], Dict[str, Any]],
        latest_marks: Dict[str, Dict[str, Any]],
        valuation_basis: str = "fair",
    ) -> float:
        equity = cash
        for (market_id, outcome), position in positions.items():
            mark = latest_marks.get(market_id)
            if not mark:
                continue
            fair_yes = float(mark["fair_probability"])
            market_yes = float(mark.get("yes_price") or fair_yes)
            if valuation_basis == "market":
                yes_value = market_yes
            elif valuation_basis == "hybrid":
                yes_value = (fair_yes + market_yes) / 2
            else:
                yes_value = fair_yes
            fair_value = yes_value if outcome == "YES" else 1 - yes_value
            equity += float(position["quantity"]) * fair_value
        return equity

    def _execution_price(self, price: float, side: str, slippage_bps: float) -> float:
        slippage = max(0.0, slippage_bps) / 10000
        adjusted = price * (1 + slippage)
        return min(0.99, max(0.01, adjusted))
