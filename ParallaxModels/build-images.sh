#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for model_dir in "${ROOT_DIR}"/*; do
  [[ -d "${model_dir}" ]] || continue
  [[ -f "${model_dir}/Dockerfile" ]] || continue
  [[ -f "${model_dir}/model.json" ]] || continue

  image="$(
    python3 - "${model_dir}/model.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    manifest = json.load(handle)
print(manifest.get("image") or "")
PY
  )"

  [[ -n "${image}" ]] || continue
  docker build -t "${image}" "${model_dir}"
done
