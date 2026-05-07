from __future__ import annotations

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_origins(value: str) -> List[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings(BaseSettings):
    API_V1_STR: str = os.getenv("PARALLAX_API_V1_STR", "/api/v1")
    PROJECT_NAME: str = os.getenv("PARALLAX_PROJECT_NAME", "Parallax")
    DB_PATH: str = os.getenv("PARALLAX_DB_PATH", "./data/parallax.db")

    POLYMARKET_GAMMA_URL: str = os.getenv(
        "POLYMARKET_GAMMA_URL", "https://gamma-api.polymarket.com"
    )
    POLYMARKET_CLOB_URL: str = os.getenv(
        "POLYMARKET_CLOB_URL", "https://clob.polymarket.com"
    )

    LUNARCHAIN_API_URL: str = os.getenv("LUNARCHAIN_API_URL", "")
    LUNARCHAIN_API_TOKEN: str = os.getenv("LUNARCHAIN_API_TOKEN", "")
    DRAFT_API_URL: str = os.getenv("DRAFT_API_URL", "")
    DRAFT_API_TOKEN: str = os.getenv("DRAFT_API_TOKEN", "")

    BINANCE_API_URL: str = os.getenv("BINANCE_API_URL", "https://api.binance.com")
    BINANCE_SYMBOLS: str = os.getenv("BINANCE_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT")
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")

    TRADING212_ENV: str = os.getenv("TRADING212_ENV", "demo")
    TRADING212_API_URL: str = os.getenv("TRADING212_API_URL", "")
    TRADING212_API_KEY: str = os.getenv("TRADING212_API_KEY", "")
    TRADING212_API_SECRET: str = os.getenv("TRADING212_API_SECRET", "")

    ENABLE_HEURISTIC_STATS: bool = os.getenv(
        "PARALLAX_ENABLE_HEURISTIC_STATS", "true"
    ).strip().lower() in {"1", "true", "yes", "on"}
    DEFAULT_MARKET_LIMIT: int = int(os.getenv("PARALLAX_DEFAULT_MARKET_LIMIT", "80"))
    MIN_EDGE: float = float(os.getenv("PARALLAX_MIN_EDGE", "0.04"))
    MODEL_REGISTRY_PATH: str = os.getenv(
        "PARALLAX_MODEL_REGISTRY_PATH",
        "../ParallaxModels",
    )

    BACKEND_CORS_ORIGINS: List[str] = _parse_origins(
        os.getenv(
            "PARALLAX_CORS_ORIGINS",
            ",".join(
                [
                    "https://parallax.lunarchain.net",
                    "https://parallax-lunarchain.web.app",
                    "http://localhost:4200",
                    "http://localhost:4201",
                    "http://localhost:4202",
                    "http://127.0.0.1:4200",
                    "http://127.0.0.1:4201",
                    "http://127.0.0.1:4202",
                    "http://localhost:8000",
                    "http://127.0.0.1:8000",
                    "http://localhost:8010",
                    "http://127.0.0.1:8010",
                ]
            ),
        )
    )

    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    @property
    def trading212_base_url(self) -> str:
        if self.TRADING212_API_URL:
            return self.TRADING212_API_URL.rstrip("/")
        if self.TRADING212_ENV.strip().lower() == "live":
            return "https://live.trading212.com/api/v0"
        return "https://demo.trading212.com/api/v0"

    @property
    def binance_symbols(self) -> List[str]:
        return _parse_origins(self.BINANCE_SYMBOLS)


settings = Settings()
