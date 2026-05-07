#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/parallax}"
REMOTE="${REMOTE:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/../ParallaxBackend"
MODELS_DIR="${SCRIPT_DIR}/../ParallaxModels"

if [[ -z "${REMOTE}" ]]; then
  echo "Set REMOTE=user@host before running this script."
  exit 1
fi

ssh "${REMOTE}" "mkdir -p ${APP_DIR}/ParallaxBackend"

rsync -az --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '.angular' \
  --exclude 'data' \
  "${BACKEND_DIR}/" "${REMOTE}:${APP_DIR}/ParallaxBackend/"

rsync -az --delete \
  --exclude '.git' \
  "${MODELS_DIR}/" "${REMOTE}:${APP_DIR}/ParallaxModels/"

ssh "${REMOTE}" "bash ${APP_DIR}/ParallaxModels/build-images.sh"
ssh "${REMOTE}" "cd ${APP_DIR}/ParallaxBackend && if docker compose version >/dev/null 2>&1; then docker compose -f docker-compose.hetzner.yml up --build -d; else docker-compose -f docker-compose.hetzner.yml build backend && docker rm -f parallaxbackend-container >/dev/null 2>&1 || true && docker-compose -f docker-compose.hetzner.yml up -d --no-deps backend && (docker ps --format '{{.Names}}' | grep -qx parallax-caddy || docker-compose -f docker-compose.hetzner.yml up -d --no-deps caddy); fi"
