#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.demo.local"
ENV_TEMPLATE="$ROOT_DIR/.env.demo.example"
COMPOSE_ARGS=(--env-file "$ENV_FILE" -f "$ROOT_DIR/docker-compose.demo.yml" -p velox-demo)
READY_TIMEOUT_SECONDS=90

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ENV_TEMPLATE" "$ENV_FILE"
  echo "Demo env dosyasi olusturuldu: $ENV_FILE"
  echo "Gerekli secret/degerleri guncelleyip komutu tekrar calistirin."
  exit 0
fi

docker compose "${COMPOSE_ARGS[@]}" up -d --build

APP_PORT="$(awk -F= '/^APP_PORT=/{print $2}' "$ENV_FILE" | tail -n1)"
APP_PORT="${APP_PORT:-8011}"

HEALTH_URL="http://127.0.0.1:${APP_PORT}/api/v1/health"
READY_URL="http://127.0.0.1:${APP_PORT}/api/v1/health/ready"
ADMIN_URL="http://127.0.0.1:${APP_PORT}/admin"

for ((i=1; i<=READY_TIMEOUT_SECONDS; i++)); do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1 && curl -fsS "$ADMIN_URL" >/dev/null 2>&1; then
    echo "Local demo hazir: $ADMIN_URL"
    if ! curl -fsS "$READY_URL" >/dev/null 2>&1; then
      echo "Not: health/ready su anda yesil degil. Bu genelde demo env'de opsiyonel entegrasyon credential'lari eksik oldugunda beklenir." >&2
      curl -sS "$READY_URL" >&2 || true
    fi
    exit 0
  fi
  sleep 1
done

echo "Local demo health/admin hazirlama zaman asimina ugradi. Son app loglari:" >&2
docker compose "${COMPOSE_ARGS[@]}" logs --tail=120 app >&2
exit 1
