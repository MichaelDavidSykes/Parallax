from __future__ import annotations

from fastapi import APIRouter

from backend.models.schemas import AutomationOut

router = APIRouter()


@router.get("", response_model=list[AutomationOut])
async def list_automations():
    return []
