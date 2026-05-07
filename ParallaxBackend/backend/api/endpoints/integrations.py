from __future__ import annotations

from fastapi import APIRouter

from backend.models.schemas import IntegrationStatus
from backend.services.integration_service import IntegrationService

router = APIRouter()


@router.get("", response_model=list[IntegrationStatus])
async def list_integrations():
    return await IntegrationService().statuses()

