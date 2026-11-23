#!/usr/bin/env bash
# =============================================================================
# CMO Agent - Health Check & Smoke Test Verification Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "================================================================="
echo "  CMO Agent Microservice - Runtime Health & Diagnostic Probe"
echo "================================================================="

# 1. Container Status Check
echo "🔍 1. Inspecting container runtime status..."
docker ps --filter "name=cmo-agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Determine accessible port (8035 mapped host port)
PROBE_PORT=8035
if curl -sf http://127.0.0.1:8035/health >/dev/null 2>&1; then
    PROBE_PORT=8035
elif curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    PROBE_PORT=8000
fi

echo ""
echo "🔍 2. Probing /health endpoint on port ${PROBE_PORT}..."
HEALTH_URL="http://127.0.0.1:${PROBE_PORT}/health"

if command -v curl >/dev/null 2>&1; then
    HEALTH_OUTPUT=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${HEALTH_URL}")
    HTTP_CODE=$(echo "${HEALTH_OUTPUT}" | grep "HTTP_STATUS" | cut -d':' -f2)
    BODY=$(echo "${HEALTH_OUTPUT}" | grep -v "HTTP_STATUS")

    if [ "${HTTP_CODE}" -eq 200 ]; then
        echo "✅ Health Probe Passed (HTTP 200 OK)"
        echo "Response Payload:"
        echo "${BODY}"
    else
        echo "❌ Health Probe Failed with HTTP status: ${HTTP_CODE}"
        echo "${BODY}"
        exit 1
    fi
else
    echo "⚠️ curl is not installed on host. Checking Docker container health status directly..."
    CONTAINER_NAME=$(docker ps --filter "name=cmo-agent" --format "{{.Names}}" | head -n 1)
    if [ -n "${CONTAINER_NAME}" ]; then
        STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "unknown")
        echo "Container ${CONTAINER_NAME} health: ${STATUS}"
        if [ "${STATUS}" != "healthy" ]; then
            exit 1
        fi
    else
        echo "❌ No CMO Agent container found running!"
        exit 1
    fi
fi

echo ""
echo "🔍 3. Probing /api/v1/health canonical endpoint..."
curl -s -i "http://127.0.0.1:${PROBE_PORT}/api/v1/health" | head -n 10 || true

echo ""
echo "================================================================="
echo "✅ All Health Checks Succeeded on Port ${PROBE_PORT}!"
echo "================================================================="
