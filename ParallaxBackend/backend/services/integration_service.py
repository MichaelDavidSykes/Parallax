from __future__ import annotations

from typing import List

from backend.core.config import settings
from backend.integrations.binance import BinanceClient
from backend.integrations.polymarket import PolymarketClient
from backend.integrations.trading212 import Trading212Client
from backend.models.schemas import IntegrationStatus


class IntegrationService:
    async def statuses(self) -> List[IntegrationStatus]:
        polymarket_status = "unknown"
        try:
            health = await PolymarketClient(
                settings.POLYMARKET_GAMMA_URL,
                settings.POLYMARKET_CLOB_URL,
            ).health()
            polymarket_status = "online" if health["ok"] else "degraded"
        except Exception:
            polymarket_status = "unreachable"

        binance_status = "unknown"
        try:
            health = await BinanceClient(settings.BINANCE_API_URL).health()
            binance_status = "online" if health["ok"] else "degraded"
        except Exception:
            binance_status = "unreachable"

        trading212 = Trading212Client(
            settings.trading212_base_url,
            settings.TRADING212_API_KEY,
            settings.TRADING212_API_SECRET,
        )
        trading212_health = await trading212.health()
        trading212_status = str(trading212_health.get("status") or "unknown")

        return [
            IntegrationStatus(
                name="Polymarket Gamma/CLOB",
                configured=True,
                status=polymarket_status,
                endpoint=settings.POLYMARKET_GAMMA_URL,
            ),
            IntegrationStatus(
                name="Binance Spot",
                configured=True,
                status=binance_status,
                endpoint=settings.BINANCE_API_URL,
            ),
            IntegrationStatus(
                name="Trading 212",
                configured=trading212.configured,
                status=trading212_status,
                endpoint=settings.trading212_base_url,
            ),
            IntegrationStatus(
                name="LunarChain API",
                configured=bool(settings.LUNARCHAIN_API_URL),
                status="configured" if settings.LUNARCHAIN_API_URL else "not configured",
                endpoint=settings.LUNARCHAIN_API_URL,
            ),
            IntegrationStatus(
                name="Draft database API",
                configured=bool(settings.DRAFT_API_URL),
                status="configured" if settings.DRAFT_API_URL else "not configured",
                endpoint=settings.DRAFT_API_URL,
            ),
            IntegrationStatus(
                name="Heuristic stats fallback",
                configured=settings.ENABLE_HEURISTIC_STATS,
                status="enabled" if settings.ENABLE_HEURISTIC_STATS else "disabled",
                endpoint="local strategy prior",
            ),
        ]
