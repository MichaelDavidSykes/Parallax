from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from backend.core.config import settings


class ModelRegistryService:
    def __init__(self, registry_path: str | None = None):
        self.registry_path = registry_path or settings.MODEL_REGISTRY_PATH

    def list(self) -> List[Dict[str, Any]]:
        models = [self._builtin_stat_arb()]
        if os.path.isdir(self.registry_path):
            for name in sorted(os.listdir(self.registry_path)):
                manifest_path = os.path.join(self.registry_path, name, "model.json")
                if not os.path.isfile(manifest_path):
                    continue
                try:
                    with open(manifest_path, "r", encoding="utf-8") as handle:
                        manifest = json.load(handle)
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(manifest, dict) and manifest.get("id"):
                    models = [model for model in models if model["id"] != manifest["id"]]
                    models.append(self._normalize_manifest(manifest))
        return models

    def get(self, model_id: str) -> Dict[str, Any]:
        for model in self.list():
            if model["id"] == model_id:
                return model
        raise ValueError(f"Unknown model: {model_id}")

    def _normalize_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(manifest.get("id")),
            "name": str(manifest.get("name") or manifest.get("id")),
            "description": str(manifest.get("description") or ""),
            "runtime": str(manifest.get("runtime") or "container"),
            "image": str(manifest.get("image") or ""),
            "strategy": str(manifest.get("strategy") or manifest.get("id")),
            "status": str(manifest.get("status") or "available"),
            "parameters": manifest.get("parameters") if isinstance(manifest.get("parameters"), list) else [],
        }

    def _builtin_stat_arb(self) -> Dict[str, Any]:
        return {
            "id": "stat_arb_v1",
            "name": "Stat Arb V1",
            "description": "Baseline probability-vs-market edge model.",
            "runtime": "builtin",
            "image": "parallax-model-stat-arb-v1",
            "strategy": "stat_arb_v1",
            "status": "available",
            "parameters": [
                {
                    "key": "min_edge",
                    "label": "Min edge",
                    "kind": "number",
                    "default": 0.04,
                    "min": 0,
                    "max": 1,
                    "step": 0.01,
                },
                {
                    "key": "max_position_pct",
                    "label": "Max position pct",
                    "kind": "number",
                    "default": 0.08,
                    "min": 0.01,
                    "max": 1,
                    "step": 0.01,
                },
                {
                    "key": "fee_bps",
                    "label": "Fee bps",
                    "kind": "number",
                    "default": 0,
                    "min": 0,
                    "step": 1,
                },
                {
                    "key": "slippage_bps",
                    "label": "Slippage bps",
                    "kind": "number",
                    "default": 0,
                    "min": 0,
                    "step": 1,
                },
                {
                    "key": "valuation_basis",
                    "label": "Mark basis",
                    "kind": "select",
                    "default": "fair",
                    "options": ["fair", "market", "hybrid"],
                },
            ],
        }
