from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx


class BinanceClient:
    def __init__(self, base_url: str, timeout: float = 12):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/v3/ping")
        return {"status_code": response.status_code, "ok": response.is_success}

    async def ticker_prices(self, symbols: List[str]) -> List[Dict[str, Any]]:
        cleaned_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if not cleaned_symbols:
                response = await client.get(f"{self.base_url}/api/v3/ticker/price")
            elif len(cleaned_symbols) == 1:
                response = await client.get(
                    f"{self.base_url}/api/v3/ticker/price",
                    params={"symbol": cleaned_symbols[0]},
                )
            else:
                response = await client.get(
                    f"{self.base_url}/api/v3/ticker/price",
                    params={"symbols": json.dumps(cleaned_symbols, separators=(",", ":"))},
                )
            response.raise_for_status()
            payload = response.json()

        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            return []
        return [self._normalize_ticker(item) for item in payload if isinstance(item, dict)]

    def _normalize_ticker(self, item: Dict[str, Any]) -> Dict[str, Any]:
        price = item.get("price")
        try:
            numeric_price = float(price)
        except (TypeError, ValueError):
            numeric_price = 0
        return {
            "symbol": str(item.get("symbol") or ""),
            "price": numeric_price,
            "source": "binance-spot",
        }
