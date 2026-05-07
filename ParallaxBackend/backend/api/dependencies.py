from __future__ import annotations

from fastapi import Request

from backend.db.database import Database


def get_database(request: Request) -> Database:
    return request.app.state.db

