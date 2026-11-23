#!/usr/bin/env bash
# =============================================================================
# CMO Agent - Production / Local Deployment Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "================================================================="
echo "  Deploying CMO Agent REST Microservice (Path B)"
echo "================================================================="

# Pre-flight check: Docker and Docker Compose
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Error: Docker is not installed or not in PATH."
    exit 1
fi

# Environment check
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        echo "⚠️ .env not found. Copying from .env.production..."
        cp .env.production .env
    elif [ -f .env.example ]; then
        echo "⚠️ .env not found. Copying from .env.example..."
        cp .env.example .env
    else
        echo "❌ Error: No .env, .env.production, or .env.example found!"
        exit 1
    fi
fi

# Ensure storage directories exist
mkdir -p data/workflow_records logs
chmod -R 777 logs data/workflow_records 2>/dev/null || true

# Determine compose file to use
COMPOSE_FILE="docker-compose.yml"
if [ "${1:-}" == "--prod" ] || [ "${ENVIRONMENT:-}" == "production" ]; then
    if [ -f "docker-compose.production.yml" ]; then
        COMPOSE_FILE="docker-compose.production.yml"
    fi
fi

echo "📦 Using Compose file: ${COMPOSE_FILE}"
echo "🔨 Building and launching containers..."
docker compose -f "${COMPOSE_FILE}" up -d --build --remove-orphans

echo "⏳ Waiting for service to initialize..."
sleep 5

# Run health check
if [ -f "${SCRIPT_DIR}/healthcheck.sh" ]; then
    bash "${SCRIPT_DIR}/healthcheck.sh"
else
    docker compose -f "${COMPOSE_FILE}" ps
fi

echo "================================================================="
echo "✅ Deployment completed successfully!"
echo "API endpoint: http://localhost:8035/health"
echo "================================================================="
