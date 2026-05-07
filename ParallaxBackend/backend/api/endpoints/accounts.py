from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_database
from backend.db.database import Database
from backend.models.schemas import NetWorthSummaryOut
from backend.services.account_service import AccountService

router = APIRouter()


@router.get("/summary", response_model=NetWorthSummaryOut)
async def account_summary(db: Database = Depends(get_database)):
    return await AccountService(db).summary()
