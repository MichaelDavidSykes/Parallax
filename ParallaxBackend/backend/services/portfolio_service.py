from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.db.database import Database, utc_now


class PortfolioService:
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, initial_cash: float) -> Dict[str, Any]:
        portfolio = {
            "id": str(uuid4()),
            "name": name,
            "initial_cash": initial_cash,
            "cash_balance": initial_cash,
            "created_at": utc_now(),
            "positions": [],
        }
        self.db.create_portfolio(portfolio)
        return portfolio

    def list(self) -> List[Dict[str, Any]]:
        return self.db.list_portfolios()

    def get_or_create_default(self) -> Dict[str, Any]:
        portfolios = self.list()
        if portfolios:
            return portfolios[0]
        return self.create(name="Paper Alpha", initial_cash=10000)

    def trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        if not self.db.get_market(trade["market_id"]):
            raise ValueError("Market not found. Sync Polymarket markets before simulating this trade.")
        trade["simulated_at"] = utc_now()
        return self.db.record_trade(trade)

    def list_trades(self, portfolio_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        return self.db.list_trades(portfolio_id=portfolio_id, limit=limit)

