from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.core.config import settings
from backend.db.database import Database, utc_now
from backend.integrations.binance import BinanceClient
from backend.integrations.trading212 import Trading212Client


class AccountService:
    def __init__(self, db: Database):
        self.db = db

    async def summary(self) -> Dict[str, Any]:
        platforms: List[Dict[str, Any]] = []
        holdings: List[Dict[str, Any]] = []

        paper_platform, paper_holdings = self._paper_summary()
        platforms.append(paper_platform)
        holdings.extend(paper_holdings)

        binance_platform, binance_holdings = await self._binance_summary()
        platforms.append(binance_platform)
        holdings.extend(binance_holdings)

        trading212_platform, trading212_holdings = await self._trading212_summary()
        platforms.append(trading212_platform)
        holdings.extend(trading212_holdings)

        total_value = sum(float(platform["total_value"]) for platform in platforms)
        cash = sum(float(platform["cash"]) for platform in platforms)
        positions_value = sum(float(platform["positions_value"]) for platform in platforms)
        stock_performance = [
            holding for holding in holdings if holding.get("asset_type") == "stock"
        ]
        return {
            "currency": "USD",
            "total_value": total_value,
            "cash": cash,
            "positions_value": positions_value,
            "platforms": platforms,
            "holdings": holdings,
            "stock_performance": stock_performance,
            "updated_at": utc_now(),
        }

    def _paper_summary(self) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        holdings: List[Dict[str, Any]] = []
        portfolios = self.db.list_portfolios()
        cash = sum(float(portfolio.get("cash_balance") or 0) for portfolio in portfolios)
        positions_value = 0.0

        for portfolio in portfolios:
            for position in portfolio.get("positions", []):
                market = self.db.get_market(str(position.get("market_id", "")))
                if not market:
                    continue
                outcome = str(position.get("outcome") or "YES").upper()
                quantity = float(position.get("quantity") or 0)
                current_price = self._paper_market_price(market, outcome)
                avg_price = float(position.get("avg_price") or 0)
                value = quantity * current_price
                positions_value += value
                holdings.append(
                    {
                        "platform": "Parallax Paper",
                        "symbol": str(market.get("slug") or market.get("id")),
                        "name": str(market.get("question") or market.get("id")),
                        "asset_type": "prediction",
                        "quantity": quantity,
                        "avg_price": avg_price,
                        "current_price": current_price,
                        "value": value,
                        "total_return_value": (current_price - avg_price) * quantity,
                        "total_return_pct": self._pct(current_price, avg_price),
                    }
                )

        return (
            {
                "platform": "Parallax Paper",
                "configured": True,
                "status": "online",
                "currency": "USD",
                "cash": cash,
                "positions_value": positions_value,
                "total_value": cash + positions_value,
            },
            holdings,
        )

    async def _binance_summary(self) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        client = BinanceClient(
            settings.BINANCE_API_URL,
            settings.BINANCE_API_KEY,
            settings.BINANCE_API_SECRET,
        )
        if not client.configured:
            return (
                {
                    "platform": "Binance",
                    "configured": False,
                    "status": "not configured",
                    "currency": "USDT",
                    "cash": 0,
                    "positions_value": 0,
                    "total_value": 0,
                },
                [],
            )
        try:
            snapshot = await client.account_snapshot()
        except Exception:
            return (
                {
                    "platform": "Binance",
                    "configured": True,
                    "status": "unreachable",
                    "currency": "USDT",
                    "cash": 0,
                    "positions_value": 0,
                    "total_value": 0,
                },
                [],
            )
        holdings = [
            {
                "platform": "Binance",
                "symbol": str(item.get("symbol") or ""),
                "name": str(item.get("symbol") or ""),
                "asset_type": "crypto",
                "quantity": float(item.get("quantity") or 0),
                "current_price": float(item.get("price") or 0),
                "value": float(item.get("value") or 0),
            }
            for item in snapshot.get("holdings", [])
        ]
        total_value = float(snapshot.get("total_value") or 0)
        cash = sum(
            float(item.get("value") or 0)
            for item in holdings
            if item.get("symbol") in {"USDT", "USD", "USDC", "BUSD"}
        )
        return (
            {
                "platform": "Binance",
                "configured": True,
                "status": "online",
                "currency": "USDT",
                "cash": cash,
                "positions_value": max(0.0, total_value - cash),
                "total_value": total_value,
            },
            holdings,
        )

    async def _trading212_summary(self) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        client = Trading212Client(
            settings.trading212_base_url,
            settings.TRADING212_API_KEY,
            settings.TRADING212_API_SECRET,
        )
        if not client.configured:
            return (
                {
                    "platform": "Trading 212",
                    "configured": False,
                    "status": "not configured",
                    "currency": "USD",
                    "cash": 0,
                    "positions_value": 0,
                    "total_value": 0,
                },
                [],
            )
        try:
            snapshot = await client.account_snapshot()
        except Exception:
            return (
                {
                    "platform": "Trading 212",
                    "configured": True,
                    "status": "unreachable",
                    "currency": "USD",
                    "cash": 0,
                    "positions_value": 0,
                    "total_value": 0,
                },
                [],
            )

        cash_payload = snapshot.get("cash", {})
        positions = snapshot.get("positions", [])
        cash = self._first_number(cash_payload, ["free", "cash", "availableFunds"])
        positions_value = 0.0
        holdings = []
        for item in positions if isinstance(positions, list) else []:
            if not isinstance(item, dict):
                continue
            quantity = self._first_number(item, ["quantity", "ownedQuantity", "qty"])
            avg_price = self._first_number(item, ["averagePrice", "avgPrice", "average_price"])
            current_price = self._first_number(item, ["currentPrice", "price", "marketPrice"])
            explicit_value = self._first_number(item, ["value", "currentValue", "marketValue"])
            value = explicit_value if explicit_value else quantity * current_price
            positions_value += value
            holdings.append(
                {
                    "platform": "Trading 212",
                    "symbol": str(item.get("ticker") or item.get("symbol") or item.get("isin") or ""),
                    "name": str(item.get("name") or item.get("ticker") or item.get("symbol") or ""),
                    "asset_type": "stock",
                    "quantity": quantity,
                    "avg_price": avg_price or None,
                    "current_price": current_price or None,
                    "value": value,
                    "day_change_pct": self._first_number(item, ["fxPpl", "dayChangePercentage"]) or None,
                    "total_return_value": self._first_number(item, ["ppl", "profitLoss"]) or None,
                    "total_return_pct": self._pct(current_price, avg_price),
                }
            )
        total = self._first_number(cash_payload, ["total", "accountValue"]) or cash + positions_value
        return (
            {
                "platform": "Trading 212",
                "configured": True,
                "status": "online",
                "currency": str(cash_payload.get("currencyCode") or cash_payload.get("currency") or "USD"),
                "cash": cash,
                "positions_value": positions_value,
                "total_value": total,
            },
            holdings,
        )

    def _paper_market_price(self, market: Dict[str, Any], outcome: str) -> float:
        prices = market.get("outcome_prices") or []
        try:
            yes_price = float(prices[0])
        except (TypeError, ValueError, IndexError):
            yes_price = 0.5
        return yes_price if outcome == "YES" else 1 - yes_price

    def _first_number(self, payload: Dict[str, Any], keys: List[str]) -> float:
        for key in keys:
            try:
                value = float(payload.get(key))
            except (TypeError, ValueError):
                continue
            return value
        return 0.0

    def _pct(self, current: float, base: float) -> float | None:
        if not base:
            return None
        return ((current - base) / base) * 100
