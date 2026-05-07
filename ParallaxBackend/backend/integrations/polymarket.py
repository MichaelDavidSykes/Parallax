from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx


def _coerce_float(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _json_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


class PolymarketClient:
    def __init__(self, gamma_url: str, clob_url: str, timeout: float = 20):
        self.gamma_url = gamma_url.rstrip("/")
        self.clob_url = clob_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            gamma = await client.get(f"{self.gamma_url}/markets", params={"limit": 1})
            clob = await client.get(f"{self.clob_url}/ok")
        return {
            "gamma": gamma.status_code,
            "clob": clob.status_code,
            "ok": gamma.is_success and clob.is_success,
        }

    async def fetch_markets(self, limit: int = 80) -> List[Dict[str, Any]]:
        params = {
            "limit": limit,
            "active": "true",
            "closed": "false",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.gamma_url}/markets", params=params)
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, list):
            return []
        return [self.normalize_market(item) for item in payload if isinstance(item, dict)]

    def normalize_market(self, item: Dict[str, Any]) -> Dict[str, Any]:
        outcomes = [str(outcome) for outcome in _json_list(item.get("outcomes"))]
        prices = [_coerce_float(price) for price in _json_list(item.get("outcomePrices"))]
        token_ids = [str(token_id) for token_id in _json_list(item.get("clobTokenIds"))]
        market_id = str(item.get("id") or item.get("conditionId") or item.get("slug"))
        return {
            "id": market_id,
            "question": str(item.get("question") or item.get("title") or "Untitled market"),
            "slug": str(item.get("slug") or ""),
            "category": str(item.get("category") or ""),
            "active": bool(item.get("active", True)),
            "closed": bool(item.get("closed", False)),
            "end_date": item.get("endDate") or item.get("endDateIso"),
            "liquidity": _coerce_float(item.get("liquidityNum", item.get("liquidity"))),
            "volume": _coerce_float(item.get("volumeNum", item.get("volume"))),
            "image": str(item.get("image") or item.get("icon") or ""),
            "outcomes": outcomes,
            "outcome_prices": prices,
            "clob_token_ids": token_ids,
            "updated_at": str(item.get("updatedAt") or item.get("updated_at") or ""),
            "raw": item,
        }

