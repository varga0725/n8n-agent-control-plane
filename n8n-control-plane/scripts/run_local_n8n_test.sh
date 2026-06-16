#!/usr/bin/env bash
# Real end-to-end test against a throwaway, local n8n in Docker.
#
# Spins up a disposable n8n container, creates the owner + a Public-API key
# automatically, runs the full integration (destructive) + smoke (read-only)
# suites against it, then tears the container down. Nothing touches your real
# instance. Requires: Docker + Python (pytest).
#
#   bash scripts/run_local_n8n_test.sh
#
# Override the n8n image/tag if you want a specific version:
#   N8N_IMAGE=docker.n8n.io/n8nio/n8n:1.70.0 bash scripts/run_local_n8n_test.sh
set -euo pipefail

IMAGE="${N8N_IMAGE:-docker.n8n.io/n8nio/n8n:latest}"
NAME="n8n-cp-test-$$"
PORT="${N8N_PORT:-5679}"
BASE="http://localhost:${PORT}"
OWNER_EMAIL="test@example.com"
OWNER_PASS="Test-12345"          # n8n requires 8+ chars, a number and a capital
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo ">> starting disposable n8n ($IMAGE) on :$PORT"
docker run -d --name "$NAME" -p "${PORT}:5678" \
  -e N8N_PUBLIC_API_DISABLED=false \
  -e N8N_DIAGNOSTICS_ENABLED=false \
  -e N8N_USER_MANAGEMENT_DISABLED=false \
  -e N8N_ENCRYPTION_KEY=test-key-not-secret \
  "$IMAGE" >/dev/null

echo ">> waiting for n8n to come up"
for i in $(seq 1 60); do
  if curl -sf "${BASE}/healthz" >/dev/null 2>&1; then break; fi
  sleep 2
  [ "$i" = 60 ] && { echo "n8n did not become healthy"; docker logs "$NAME" | tail -20; exit 1; }
done

echo ">> creating owner account"
curl -sf -c /tmp/n8n_cookies_$$ -X POST "${BASE}/rest/owner/setup" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${OWNER_EMAIL}\",\"firstName\":\"Test\",\"lastName\":\"User\",\"password\":\"${OWNER_PASS}\"}" \
  >/dev/null || echo "   (owner may already exist — continuing)"

echo ">> logging in"
curl -sf -c /tmp/n8n_cookies_$$ -X POST "${BASE}/rest/login" \
  -H 'Content-Type: application/json' \
  -d "{\"emailOrLdapLoginId\":\"${OWNER_EMAIL}\",\"password\":\"${OWNER_PASS}\"}" >/dev/null

echo ">> creating Public API key"
API_RESP="$(curl -sf -b /tmp/n8n_cookies_$$ -X POST "${BASE}/rest/api-keys" \
  -H 'Content-Type: application/json' \
  -d '{"label":"cp-test","expiresAt":null}')"
# Field name differs across versions: rawApiKey | apiKey
KEY="$(printf '%s' "$API_RESP" | python3 -c 'import sys,json;d=json.load(sys.stdin);d=d.get("data",d);print(d.get("rawApiKey") or d.get("apiKey") or "")')"
if [ -z "$KEY" ]; then echo "could not create API key. Response: $API_RESP"; exit 1; fi
echo "   key acquired"

echo ">> running test suites against the local instance"
export N8N_BASE_URL="${BASE}/api/v1"
export N8N_API_KEY="$KEY"
export N8N_AUDIT_DIR="/tmp/cp-audit-$$"
export N8N_BACKUP_DIR="/tmp/cp-backup-$$"
export PYTHONPATH="${ROOT}/src"

set +e
echo "-- read-only smoke --"
N8N_RUN_SMOKE=1 python3 -m pytest "${ROOT}/tests/smoke" -q
SMOKE=$?
echo "-- destructive integration (disposable instance) --"
N8N_RUN_INTEGRATION=1 N8N_ALLOW_DESTRUCTIVE=1 N8N_ALLOW_PRODUCTION_WRITES=1 \
  python3 -m pytest "${ROOT}/tests/integration" -q
INTEG=$?
set -e

echo
echo "==== RESULT ===="
echo "smoke:        $([ $SMOKE -eq 0 ] && echo PASS || echo FAIL)"
echo "integration:  $([ $INTEG -eq 0 ] && echo PASS || echo FAIL)"
rm -f /tmp/n8n_cookies_$$
exit $(( SMOKE | INTEG ))
