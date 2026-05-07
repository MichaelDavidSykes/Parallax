from __future__ import annotations

from typing import List

from backend.core.config import settings
from backend.integrations.trading212 import Trading212Client
from backend.models.schemas import IntegrationStatus


class IntegrationService:
    async def statuses(self) -> List[IntegrationStatus]:
        trading212 = Trading212Client(
            settings.trading212_base_url,
            settings.TRADING212_API_KEY,
            settings.TRADING212_API_SECRET,
        )
        trading212_health = await trading212.health()
        return [
            IntegrationStatus(
                name="Trading 212",
                configured=trading212.configured,
                status=str(trading212_health.get("status") or "unknown"),
                endpoint=settings.trading212_base_url,
            )
        ]
