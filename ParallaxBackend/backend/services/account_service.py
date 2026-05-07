from __future__ import annotations

from typing import Any, Dict

from backend.db.database import Database
from backend.services.trading212_service import Trading212Service


class AccountService:
    def __init__(self, db: Database):
        self.db = db

    async def summary(self) -> Dict[str, Any]:
        trading212 = await Trading212Service().summary()
        holdings = [
            {
                "platform": "Trading 212",
                "symbol": position["symbol"],
                "name": position["name"],
                "asset_type": "stock",
                "quantity": position["quantity"],
                "avg_price": position["avg_price"],
                "current_price": position["current_price"],
                "value": position["value"],
                "total_return_pct": position["pnl_pct"],
                "total_return_value": position["pnl"],
            }
            for position in trading212["positions"]
        ]
        return {
            "currency": trading212["currency"],
            "total_value": trading212["total_value"],
            "cash": trading212["cash"],
            "positions_value": trading212["positions_value"],
            "platforms": [
                {
                    "platform": "Trading 212",
                    "configured": trading212["configured"],
                    "status": trading212["status"],
                    "currency": trading212["currency"],
                    "cash": trading212["cash"],
                    "positions_value": trading212["positions_value"],
                    "total_value": trading212["total_value"],
                }
            ],
            "holdings": holdings,
            "stock_performance": holdings,
            "updated_at": trading212["updated_at"],
        }
