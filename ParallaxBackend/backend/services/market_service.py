from __future__ import annotations

from typing import Any, Dict, List

from backend.core.config import settings
from backend.db.database import Database
from backend.integrations.polymarket import PolymarketClient


class MarketService:
    def __init__(self, db: Database):
        self.db = db
        self.client = PolymarketClient(
            gamma_url=settings.POLYMARKET_GAMMA_URL,
            clob_url=settings.POLYMARKET_CLOB_URL,
        )

    async def sync_markets(self, limit: int = 80) -> Dict[str, Any]:
        markets = await self.client.fetch_markets(limit=limit)
        stored = self.db.upsert_markets(markets)
        return {"fetched": len(markets), "stored": stored, "markets": markets}

    async def ensure_markets(self, limit: int = 80, refresh: bool = True) -> List[Dict[str, Any]]:
        if refresh:
            await self.sync_markets(limit=limit)
        markets = self.db.list_markets(limit=limit, active_only=True)
        if not markets:
            await self.sync_markets(limit=limit)
            markets = self.db.list_markets(limit=limit, active_only=True)
        return markets

    def list_markets(self, limit: int = 100, active_only: bool = True) -> List[Dict[str, Any]]:
        return self.db.list_markets(limit=limit, active_only=active_only)

