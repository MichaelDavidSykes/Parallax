from __future__ import annotations

from typing import Any, Dict, List

from backend.core.config import settings
from backend.db.database import Database, utc_now
from backend.integrations.external_stats import ExternalStatsClient, clamp
from backend.services.market_service import MarketService


class OpportunityService:
    def __init__(self, db: Database):
        self.db = db
        self.market_service = MarketService(db)
        self.stats_client = ExternalStatsClient(
            lunar_url=settings.LUNARCHAIN_API_URL,
            lunar_token=settings.LUNARCHAIN_API_TOKEN,
            draft_url=settings.DRAFT_API_URL,
            draft_token=settings.DRAFT_API_TOKEN,
            enable_heuristic_stats=settings.ENABLE_HEURISTIC_STATS,
        )

    async def scan(
        self,
        market_limit: int = 80,
        min_edge: float = 0.04,
        refresh_markets: bool = True,
    ) -> Dict[str, Any]:
        markets = await self.market_service.ensure_markets(
            limit=market_limit,
            refresh=refresh_markets,
        )
        opportunities: List[Dict[str, Any]] = []
        captured_at = utc_now()
        for market in markets:
            prices = market.get("outcome_prices") or []
            if not prices:
                continue
            try:
                yes_price = clamp(float(prices[0]))
            except (TypeError, ValueError):
                continue
            no_price = clamp(1 - yes_price)
            signal = await self.stats_client.signal_for_market(market)
            snapshot = {
                "market_id": market["id"],
                "captured_at": captured_at,
                "yes_price": yes_price,
                "no_price": no_price,
                "fair_probability": signal.fair_probability,
                "confidence": signal.confidence,
                "source": signal.source,
                "liquidity": market.get("liquidity", 0),
                "volume": market.get("volume", 0),
                "raw": {"signal": signal.raw, "rationale": signal.rationale},
            }
            self.db.insert_snapshot(snapshot)
            edge = signal.fair_probability - yes_price
            if abs(edge) < min_edge:
                continue
            side = "BUY_YES" if edge > 0 else "BUY_NO"
            trade_price = yes_price if side == "BUY_YES" else no_price
            max_stake = max(5, min(500, float(market.get("liquidity") or 0) * 0.01))
            opportunities.append(
                {
                    "market_id": market["id"],
                    "detected_at": captured_at,
                    "side": side,
                    "market_price": trade_price,
                    "fair_probability": signal.fair_probability,
                    "edge": edge,
                    "expected_value": abs(edge) * signal.confidence,
                    "confidence": signal.confidence,
                    "max_stake": max_stake,
                    "rationale": signal.rationale,
                }
            )
        self.db.replace_opportunities(opportunities)
        return {
            "scanned": len(markets),
            "created": len(opportunities),
            "opportunities": self.db.list_opportunities(limit=market_limit),
        }

    def list_opportunities(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.db.list_opportunities(limit=limit)

