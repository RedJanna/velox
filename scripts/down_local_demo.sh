#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.demo.local"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Demo env dosyasi bulunamadi: $ENV_FILE"
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/docker-compose.demo.yml" -p velox-demo down
