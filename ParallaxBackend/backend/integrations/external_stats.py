from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


def clamp(value: float, lower: float = 0.01, upper: float = 0.99) -> float:
    return max(lower, min(upper, value))


@dataclass
class StatsSignal:
    fair_probability: float
    confidence: float
    source: str
    rationale: str
    raw: Dict[str, Any]


class ExternalStatsClient:
    def __init__(
        self,
        lunar_url: str = "",
        lunar_token: str = "",
        draft_url: str = "",
        draft_token: str = "",
        enable_heuristic_stats: bool = True,
        timeout: float = 12,
    ):
        self.lunar_url = lunar_url.rstrip("/")
        self.lunar_token = lunar_token
        self.draft_url = draft_url.rstrip("/")
        self.draft_token = draft_token
        self.enable_heuristic_stats = enable_heuristic_stats
        self.timeout = timeout

    async def signal_for_market(self, market: Dict[str, Any]) -> StatsSignal:
        draft_signal = await self._draft_signal(market)
        if draft_signal:
            return draft_signal
        lunar_signal = await self._lunar_signal(market)
        if lunar_signal:
            return lunar_signal
        return self._heuristic_signal(market)

    async def _draft_signal(self, market: Dict[str, Any]) -> Optional[StatsSignal]:
        if not self.draft_url:
            return None
        headers = {}
        if self.draft_token:
            headers["Authorization"] = f"Bearer {self.draft_token}"
        params = {"slug": market.get("slug", ""), "question": market.get("question", "")}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.draft_url}/probabilities",
                    params=params,
                    headers=headers,
                )
            if not response.is_success:
                return None
            payload = response.json()
        except Exception:
            return None
        signal = self._parse_probability_payload(payload, "draft-database")
        return signal

    async def _lunar_signal(self, market: Dict[str, Any]) -> Optional[StatsSignal]:
        if not self.lunar_url:
            return None
        headers = {}
        if self.lunar_token:
            headers["Authorization"] = f"Bearer {self.lunar_token}"
        params = {"slug": market.get("slug", ""), "market_id": market.get("id", "")}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.lunar_url}/api/v1/signals/polymarket",
                    params=params,
                    headers=headers,
                )
            if not response.is_success:
                return None
            payload = response.json()
        except Exception:
            return None
        signal = self._parse_probability_payload(payload, "lunarchain-api")
        return signal

    def _parse_probability_payload(
        self,
        payload: Any,
        source: str,
    ) -> Optional[StatsSignal]:
        if not isinstance(payload, dict):
            return None
        value = (
            payload.get("fair_probability")
            or payload.get("probability")
            or payload.get("yes_probability")
        )
        try:
            fair_probability = clamp(float(value))
        except (TypeError, ValueError):
            return None
        try:
            confidence = clamp(float(payload.get("confidence", 0.72)), 0.01, 1)
        except (TypeError, ValueError):
            confidence = 0.72
        return StatsSignal(
            fair_probability=fair_probability,
            confidence=confidence,
            source=source,
            rationale=str(payload.get("rationale") or "External probability signal"),
            raw=payload,
        )

    def _heuristic_signal(self, market: Dict[str, Any]) -> StatsSignal:
        prices = market.get("outcome_prices") or []
        try:
            market_price = float(prices[0])
        except (TypeError, ValueError, IndexError):
            market_price = 0.5

        if not self.enable_heuristic_stats:
            return StatsSignal(
                fair_probability=clamp(market_price),
                confidence=0.2,
                source="market-only",
                rationale="No external stats provider configured; using current market probability.",
                raw={},
            )

        seed_text = f"{market.get('slug', '')}:{market.get('question', '')}"
        digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
        centered = (int(digest[:8], 16) / 0xFFFFFFFF) - 0.5
        liquidity = float(market.get("liquidity") or 0)
        volume = float(market.get("volume") or 0)
        liquidity_conf = min(0.2, liquidity / 500000)
        volume_conf = min(0.18, volume / 2500000)
        drift = centered * 0.16
        fair_probability = clamp(market_price + drift)
        return StatsSignal(
            fair_probability=fair_probability,
            confidence=0.38 + liquidity_conf + volume_conf,
            source="heuristic-stats",
            rationale=(
                "Fallback statistical prior; configure Draft or LunarChain APIs "
                "to replace this with observed real-world stats."
            ),
            raw={"hash_drift": drift, "liquidity": liquidity, "volume": volume},
        )

