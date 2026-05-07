from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Tuple

from dateutil import parser

from backend.core.config import settings
from backend.db.database import utc_now
from backend.integrations.trading212 import Trading212Client


class Trading212Service:
    def __init__(self):
        self.client = Trading212Client(
            settings.trading212_base_url,
            settings.TRADING212_API_KEY,
            settings.TRADING212_API_SECRET,
        )

    async def summary(self) -> Dict[str, Any]:
        if not self.client.configured:
            return self._empty_summary("not configured")

        try:
            summary = await self.client.account_summary()
            cash_payload = await self.client.account_cash()
            positions_payload = await self.client.portfolio()
            trades_payload = await self.client.historical_orders(limit=50, max_pages=3)
        except Exception:
            return self._empty_summary("unreachable", configured=True)

        positions = [self._normalize_position(item) for item in positions_payload]
        positions = [position for position in positions if position["symbol"]]
        trades = [self._normalize_trade(item) for item in trades_payload]
        trades = [trade for trade in trades if trade["symbol"]]
        trades.sort(key=lambda trade: trade.get("executed_at") or "", reverse=True)

        cash = self._first_number_recursive(
            [summary, cash_payload],
            ["free", "cash", "availableFunds", "availableToTrade", "available"],
        )
        positions_value = sum(float(position["value"]) for position in positions)
        explicit_total = self._first_number_recursive(
            [summary, cash_payload],
            ["accountValue", "portfolioValue", "totalValue", "total", "value"],
        )
        total_value = explicit_total or cash + positions_value
        total_pnl = sum(float(position.get("pnl") or 0) for position in positions)
        invested_value = sum(
            float(position.get("avg_price") or 0) * float(position.get("quantity") or 0)
            for position in positions
        )

        return {
            "configured": True,
            "status": "online",
            "platform": "Trading 212",
            "currency": self._currency(summary, cash_payload, positions),
            "cash": cash,
            "positions_value": positions_value,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": self._pct(total_pnl, invested_value),
            "positions": positions,
            "trades": trades,
            "updated_at": utc_now(),
        }

    async def chart(self, ticker: str = "", timeframe: str = "1M") -> Dict[str, Any]:
        if not self.client.configured:
            return self._empty_chart(ticker=ticker, timeframe=timeframe, status="not configured")

        try:
            positions_payload = await self.client.portfolio()
            requested_ticker = ticker or self._first_ticker(positions_payload)
            trades_payload = await self.client.historical_orders(
                ticker=requested_ticker,
                limit=50,
                max_pages=5,
            )
        except Exception:
            return self._empty_chart(ticker=ticker, timeframe=timeframe, status="unreachable", configured=True)

        positions = [self._normalize_position(item) for item in positions_payload]
        trades = [self._normalize_trade(item) for item in trades_payload]
        if not requested_ticker:
            requested_ticker = self._first_trade_ticker(trades)
        if requested_ticker:
            positions = [item for item in positions if item["symbol"] == requested_ticker]
            trades = [item for item in trades if item["symbol"] == requested_ticker]

        candles, line = self._build_trade_chart(
            trades=trades,
            current_price=positions[0]["current_price"] if positions else None,
            timeframe=timeframe,
        )
        return {
            "configured": True,
            "status": "online",
            "ticker": requested_ticker,
            "timeframe": timeframe,
            "candles": candles,
            "line": line,
            "trades": sorted(trades, key=lambda trade: trade.get("executed_at") or ""),
        }

    async def market_order(
        self,
        ticker: str,
        side: str,
        quantity: float,
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        signed_quantity = abs(quantity)
        if side.upper() == "SELL":
            signed_quantity *= -1
        return await self.client.market_order(
            ticker=ticker,
            quantity=signed_quantity,
            extended_hours=extended_hours,
        )

    def _empty_summary(self, status: str, configured: bool = False) -> Dict[str, Any]:
        return {
            "configured": configured,
            "status": status,
            "platform": "Trading 212",
            "currency": "USD",
            "cash": 0,
            "positions_value": 0,
            "total_value": 0,
            "total_pnl": 0,
            "total_pnl_pct": None,
            "positions": [],
            "trades": [],
            "updated_at": utc_now(),
        }

    def _empty_chart(
        self,
        ticker: str,
        timeframe: str,
        status: str,
        configured: bool = False,
    ) -> Dict[str, Any]:
        return {
            "configured": configured,
            "status": status,
            "ticker": ticker,
            "timeframe": timeframe,
            "candles": [],
            "line": [],
            "trades": [],
        }

    def _normalize_position(self, item: Dict[str, Any]) -> Dict[str, Any]:
        instrument = item.get("instrument") if isinstance(item.get("instrument"), dict) else {}
        wallet = item.get("walletImpact") if isinstance(item.get("walletImpact"), dict) else {}
        symbol = str(item.get("ticker") or item.get("symbol") or instrument.get("ticker") or "")
        quantity = self._first_number(item, ["quantity", "ownedQuantity", "qty"])
        avg_price = self._first_number(item, ["averagePricePaid", "averagePrice", "avgPrice", "average_price"])
        current_price = self._first_number(item, ["currentPrice", "price", "marketPrice"])
        explicit_value = self._first_number(item, ["value", "currentValue", "marketValue"]) or self._first_number(
            wallet,
            ["currentValue", "marketValue", "value"],
        )
        value = explicit_value or quantity * current_price
        pnl = self._first_number(item, ["ppl", "profitLoss", "result", "unrealizedPnl"]) or self._first_number(
            wallet,
            ["ppl", "profitLoss", "result", "unrealizedPnl"],
        )
        if not pnl and avg_price and current_price:
            pnl = (current_price - avg_price) * quantity
        invested = avg_price * quantity
        return {
            "symbol": symbol,
            "name": str(item.get("name") or instrument.get("name") or symbol),
            "currency": str(item.get("currency") or instrument.get("currency") or "USD"),
            "quantity": quantity,
            "avg_price": avg_price or None,
            "current_price": current_price or None,
            "value": value,
            "pnl": pnl,
            "pnl_pct": self._pct(pnl, invested),
        }

    def _normalize_trade(self, item: Dict[str, Any]) -> Dict[str, Any]:
        instrument = item.get("instrument") if isinstance(item.get("instrument"), dict) else {}
        symbol = str(item.get("ticker") or item.get("symbol") or instrument.get("ticker") or "")
        raw_quantity = self._first_number(item, ["filledQuantity", "quantity", "qty"])
        side = str(item.get("side") or ("SELL" if raw_quantity < 0 else "BUY")).upper()
        quantity = abs(raw_quantity)
        value = self._first_number(item, ["filledValue", "value", "total", "amount"])
        price = self._first_number(item, ["averagePrice", "filledPrice", "fillPrice", "price", "limitPrice"])
        if not price and value and quantity:
            price = abs(value / quantity)
        executed_at = str(
            item.get("executedAt")
            or item.get("filledAt")
            or item.get("createdAt")
            or item.get("date")
            or ""
        )
        return {
            "id": str(item.get("id") or item.get("orderId") or ""),
            "symbol": symbol,
            "name": str(item.get("name") or instrument.get("name") or symbol),
            "side": "SELL" if side == "SELL" or raw_quantity < 0 else "BUY",
            "quantity": quantity,
            "price": price,
            "value": abs(value) if value else quantity * price,
            "status": str(item.get("status") or ""),
            "type": str(item.get("type") or "MARKET"),
            "executed_at": executed_at,
        }

    def _build_trade_chart(
        self,
        trades: List[Dict[str, Any]],
        current_price: float | None,
        timeframe: str,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        bucket_seconds = self._bucket_seconds(timeframe)
        cutoff = self._cutoff(timeframe)
        buckets: Dict[int, List[float]] = defaultdict(list)
        for trade in trades:
            timestamp = self._parse_datetime(str(trade.get("executed_at") or ""))
            price = float(trade.get("price") or 0)
            if not timestamp or price <= 0 or (cutoff and timestamp < cutoff):
                continue
            bucket = int(timestamp.timestamp()) // bucket_seconds * bucket_seconds
            buckets[bucket].append(price)

        candles = []
        for bucket in sorted(buckets):
            prices = buckets[bucket]
            candles.append(
                {
                    "time": bucket,
                    "open": prices[0],
                    "high": max(prices),
                    "low": min(prices),
                    "close": prices[-1],
                }
            )
        if current_price and candles:
            now_bucket = int(datetime.now(timezone.utc).timestamp()) // bucket_seconds * bucket_seconds
            last_close = float(candles[-1]["close"])
            candles.append(
                {
                    "time": max(now_bucket, int(candles[-1]["time"]) + bucket_seconds),
                    "open": last_close,
                    "high": max(last_close, current_price),
                    "low": min(last_close, current_price),
                    "close": current_price,
                }
            )
        line = [{"time": item["time"], "value": item["close"]} for item in candles]
        return candles, line

    def _bucket_seconds(self, timeframe: str) -> int:
        return {
            "1D": 60 * 60,
            "1W": 4 * 60 * 60,
            "1M": 24 * 60 * 60,
            "3M": 24 * 60 * 60,
            "1Y": 7 * 24 * 60 * 60,
            "ALL": 30 * 24 * 60 * 60,
        }.get(timeframe.upper(), 24 * 60 * 60)

    def _cutoff(self, timeframe: str) -> datetime | None:
        now = datetime.now(timezone.utc)
        return {
            "1D": now - timedelta(days=1),
            "1W": now - timedelta(days=7),
            "1M": now - timedelta(days=31),
            "3M": now - timedelta(days=93),
            "1Y": now - timedelta(days=366),
        }.get(timeframe.upper())

    def _parse_datetime(self, value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = parser.parse(value)
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _first_ticker(self, positions: Iterable[Dict[str, Any]]) -> str:
        for item in positions:
            position = self._normalize_position(item)
            if position["symbol"]:
                return str(position["symbol"])
        return ""

    def _first_trade_ticker(self, trades: Iterable[Dict[str, Any]]) -> str:
        for item in trades:
            symbol = str(item.get("symbol") or "")
            if symbol:
                return symbol
        return ""

    def _currency(
        self,
        summary: Dict[str, Any],
        cash: Dict[str, Any],
        positions: List[Dict[str, Any]],
    ) -> str:
        for payload in (summary, cash):
            for key in ("currency", "currencyCode", "mainCurrency"):
                if payload.get(key):
                    return str(payload[key])
        for position in positions:
            instrument = position.get("instrument")
            if isinstance(instrument, dict) and instrument.get("currency"):
                return str(instrument["currency"])
        return "USD"

    def _first_number_recursive(self, payloads: Iterable[Any], keys: List[str]) -> float:
        for payload in payloads:
            value = self._find_number(payload, keys)
            if value:
                return value
        return 0.0

    def _find_number(self, payload: Any, keys: List[str]) -> float:
        if isinstance(payload, dict):
            for key in keys:
                if key in payload:
                    value = self._coerce_float(payload.get(key))
                    if value:
                        return value
            for value in payload.values():
                found = self._find_number(value, keys)
                if found:
                    return found
        if isinstance(payload, list):
            for item in payload:
                found = self._find_number(item, keys)
                if found:
                    return found
        return 0.0

    def _first_number(self, payload: Dict[str, Any], keys: List[str]) -> float:
        for key in keys:
            value = self._coerce_float(payload.get(key))
            if value:
                return value
        return 0.0

    def _coerce_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _pct(self, value: float, base: float) -> float | None:
        if not base:
            return None
        return (value / base) * 100
