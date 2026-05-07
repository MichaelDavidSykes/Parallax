from __future__ import annotations

from typing import List

from backend.core.config import settings
from backend.integrations.polymarket import PolymarketClient
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

        return [
            IntegrationStatus(
                name="Polymarket Gamma/CLOB",
                configured=True,
                status=polymarket_status,
                endpoint=settings.POLYMARKET_GAMMA_URL,
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

