from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional

import httpx

try:
    from prefect import flow, get_run_logger, task
except ImportError:
    logging.basicConfig(level=logging.INFO)

    def flow(*_args, **_kwargs):
        def decorator(fn):
            return fn

        return decorator

    def task(*_args, **_kwargs):
        def decorator(fn):
            return fn

        return decorator

    def get_run_logger():
        return logging.getLogger("parallax-engine")


def _backend_url(override: Optional[str] = None) -> str:
    return (override or os.getenv("PARALLAX_BACKEND_URL", "http://localhost:8010")).rstrip("/")


@task(name="Parallax API Request", retries=2, retry_delay_seconds=10)
def api_request(
    method: str,
    path: str,
    backend_url: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    logger = get_run_logger()
    url = f"{backend_url}/api/v1{path}"
    logger.info("%s %s", method.upper(), url)
    with httpx.Client(timeout=120) as client:
        response = client.request(
            method=method,
            url=url,
            json=payload,
            params=params,
        )
    response.raise_for_status()
    data = response.json()
    logger.info("Completed %s %s", method.upper(), path)
    return data


@flow(name="parallax-ingestion-pipeline", log_prints=True)
def parallax_ingestion_pipeline(
    market_limit: int = 80,
    min_edge: float = 0.04,
    backend_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    LunarEngine-style orchestration for Parallax:
    Polymarket sync -> stats scan -> opportunity persistence.
    """
    resolved_backend = _backend_url(backend_url)
    sync_result = api_request(
        method="POST",
        path="/markets/sync",
        backend_url=resolved_backend,
        params={"limit": market_limit},
    )
    scan_result = api_request(
        method="POST",
        path="/opportunities/scan",
        backend_url=resolved_backend,
        payload={
            "market_limit": market_limit,
            "min_edge": min_edge,
            "refresh_markets": False,
        },
    )
    return {
        "backend_url": resolved_backend,
        "markets": sync_result,
        "opportunities": scan_result,
    }


@flow(name="parallax-backtest-pipeline", log_prints=True)
def parallax_backtest_pipeline(
    name: str = "Prefect stat arb replay",
    initial_cash: float = 10000,
    market_limit: int = 100,
    min_edge: float = 0.04,
    max_position_pct: float = 0.08,
    fee_bps: float = 0,
    backend_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Runs a fresh scan and then asks the backend to persist a backtest run.
    """
    resolved_backend = _backend_url(backend_url)
    ingestion = parallax_ingestion_pipeline(
        market_limit=market_limit,
        min_edge=min_edge,
        backend_url=resolved_backend,
    )
    backtest = api_request(
        method="POST",
        path="/backtests",
        backend_url=resolved_backend,
        payload={
            "name": name,
            "strategy": "stat_arb_v1",
            "initial_cash": initial_cash,
            "market_limit": market_limit,
            "min_edge": min_edge,
            "max_position_pct": max_position_pct,
            "fee_bps": fee_bps,
            "refresh_markets": False,
        },
    )
    return {
        "backend_url": resolved_backend,
        "ingestion": ingestion,
        "backtest": backtest,
    }
