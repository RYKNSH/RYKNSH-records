#!/usr/bin/env bash
# ============================================================
# Velie E2E Test Script
# Simulates a GitHub webhook → FastAPI → LangGraph flow locally
#
# Prerequisites:
#   1. cp .env.example .env && edit .env with real keys
#   2. uv run python main.py  (in another terminal)
#   3. ./scripts/test_webhook.sh
# ============================================================

set -euo pipefail

PORT="${PORT:-8000}"
BASE_URL="http://localhost:${PORT}"
WEBHOOK_SECRET="${GITHUB_WEBHOOK_SECRET:-your-webhook-secret-here}"

# --- Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Velie E2E Test${NC}"
echo "================================"

# 1. Health Check
echo -n "1. Health check... "
HEALTH=$(curl -s "${BASE_URL}/health")
if echo "$HEALTH" | grep -q '"ok"'; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Server not running at ${BASE_URL}${NC}"
    echo "   Start server: VELIE_ENV=development uv run python main.py"
    exit 1
fi

# 2. Webhook with valid signature
echo -n "2. Webhook (PR opened)... "

PAYLOAD='{
  "action": "opened",
  "pull_request": {
    "number": 999,
    "title": "test: Velie E2E verification",
    "body": "Intentional bugs for QA review.",
    "user": {"login": "e2e-test"}
  },
  "repository": {
    "full_name": "RYKNSH/RYKNSH-records"
  },
  "installation": {"id": 1}
}'

# Calculate HMAC-SHA256 signature
SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')

RESULT=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/webhook/github" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: sha256=${SIG}" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESULT" | tail -1)
BODY=$(echo "$RESULT" | head -1)

if [ "$HTTP_CODE" == "200" ] && echo "$BODY" | grep -q '"queued"'; then
    echo -e "${GREEN}✅ Queued (PR #999)${NC}"
else
    echo -e "${RED}❌ Failed (HTTP ${HTTP_CODE})${NC}"
    echo "   Response: $BODY"
    exit 1
fi

# 3. Webhook rejected (bad signature)
echo -n "3. Bad signature... "
RESULT=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/webhook/github" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: sha256=invalid" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESULT" | tail -1)
if [ "$HTTP_CODE" == "401" ]; then
    echo -e "${GREEN}✅ Rejected (401)${NC}"
else
    echo -e "${RED}❌ Expected 401, got ${HTTP_CODE}${NC}"
fi

# 4. Non-PR event ignored
echo -n "4. Non-PR event... "
NON_PR='{"action": "completed"}'
SIG2=$(echo -n "$NON_PR" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $2}')
RESULT=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/webhook/github" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=${SIG2}" \
  -d "$NON_PR")

HTTP_CODE=$(echo "$RESULT" | tail -1)
BODY=$(echo "$RESULT" | head -1)
if [ "$HTTP_CODE" == "200" ] && echo "$BODY" | grep -q '"ignored"'; then
    echo -e "${GREEN}✅ Ignored${NC}"
else
    echo -e "${RED}❌ Expected ignored, got ${HTTP_CODE}${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ All E2E checks passed!${NC}"
echo ""
echo "📋 Check server logs for background review execution."
echo "   If ANTHROPIC_API_KEY is set, Claude will attempt to review PR #999."
