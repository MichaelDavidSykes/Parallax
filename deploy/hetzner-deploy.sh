#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/parallax}"
REMOTE="${REMOTE:-}"

if [[ -z "${REMOTE}" ]]; then
  echo "Set REMOTE=user@host before running this script."
  exit 1
fi

rsync -az --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '.angular' \
  --exclude 'data' \
  ../ParallaxBackend/ "${REMOTE}:${APP_DIR}/ParallaxBackend/"

ssh "${REMOTE}" "cd ${APP_DIR}/ParallaxBackend && docker compose up --build -d"

