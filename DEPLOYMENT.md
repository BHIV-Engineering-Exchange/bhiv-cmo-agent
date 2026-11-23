# CMO Agent - DevOps Production Deployment Infrastructure

This document details the complete deployment infrastructure, operational runbook, and CI/CD automation pipeline for the **CMO Agent Path B REST Microservice** (`bhiv-cmo-agent`), aligning with BHIV infrastructure standards established across sister platforms (**ARTHA**, **Samruddhi**, and **Gurukul**).

---

## 1. System Overview & Architecture

- **Service Name**: `cmo-agent-api` (CMO Agent Path B Microservice)
- **Role**: Evidence-grounded marketing intelligence RAG, policy question-answering, and managerial approval governance engine.
- **Runtime & Framework**: Python 3.11-slim running ASGI via Uvicorn.
- **Security Context**: Dedicated non-root service account `cmo:cmo` (UID/GID: `10001`).
- **Direct Database**: None (stateless compute with persistent volume mounts for proposal records and runtime audit logs).
- **Upstream Dependencies**: MASTERDB platform service (`cap-cmo-marketing-intelligence`). Includes automatic local fallback adapter for resilient offline execution.
- **Reverse Proxy / SSL**: Handled by the centralized Nginx proxy service running across the host system (`nginx.ssl.conf`), routing external requests to `127.0.0.1:8035`.

### Port Matrix

| Service | Container Port | Host Port | Protocol | Notes |
|---|---|---|---|---|
| `cmo-agent-api` | `8000` | **`8035`** | TCP / HTTP | Host port `8035` mapped to avoid port `8000` conflict on VM |
| `masterdb` (mock/local) | `8000` | `8036` | TCP / HTTP | Optional local test mock service |

---

## 2. Directory Structure of Deployment Infrastructure

```
bhiv-cmo-agent/
├── .github/
│   └── workflows/
│       └── cicd.yml                        # GitHub Actions CI/CD Pipeline (Validate, Build, Deploy, Rollback)
├── docs/
│   └── RELEASE_HISTORY.md                 # Production release registry & rollback reference
├── scripts/
│   ├── deploy.sh                          # Local / VM deploy helper
│   ├── healthcheck.sh                     # Runtime health & smoke probe tester
│   ├── rollback.sh                        # Automated & manual rollback executor
│   ├── restart.sh                         # Stack restart helper
│   ├── stop.sh                            # Clean shutdown script
│   └── logs.sh                            # Log streaming utility
├── .env.example                           # Documented environment template
├── Dockerfile                             # Hardened multi-stage OCI container definition
├── Dockerfile.prod                        # Production container image definition
├── docker-compose.yml                     # Local / testing orchestration stack (mapped port 8035:8000)
├── docker-compose.production.template.yml # Production deployment template (mapped port 8035:8000)
└── DEPLOYMENT.md                          # Comprehensive DevOps infrastructure manual
```

---

## 3. Environment Secret Management

In accordance with BHIV security standards, environment variables and secret values are **not exposed** in Docker Compose manifests. Instead:
- Docker Compose loads configurations exclusively via `env_file: - .env`.
- During CI/CD deployment, GitHub Actions dynamically injects the `.env` file from the **`CMO_ENV_FILE`** repository secret.

### Environment Specification Reference

```bash
# Server Settings
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000

# Auth & Governance
API_AUTH_ENABLED=true
AUTH_STRICT_RS256=false

# MASTERDB Endpoint & Capability
MASTERDB_URL=http://127.0.0.1:8000
MASTERDB_APP_ID=CMO_AGENT
MASTERDB_CAPABILITY_ID=cap-cmo-marketing-intelligence

# Storage, Logging & RAG Engine
RAG_LOG_LEVEL=INFO
RAG_LOG_FILE=/app/logs/cmo_service.log
RAG_RANDOM_SEED=42
RAG_GENERATION_MODE=mock
```

---

## 4. Containerization & Production Standards

The container conforms to BHIV cloud-native specifications:
1. **Base Image**: `python:3.11-slim` for minimal vulnerability footprint and fast image pull times.
2. **Deterministic Binary Pinning**: Pins `numpy==1.26.4` before installing `requirements.txt` to guarantee reproducible dot-product calculations.
3. **Least-Privilege Security**: Runs as unprivileged user `cmo:cmo` (UID 10001).
4. **Health Check**: Native Docker health check monitoring `curl -f http://127.0.0.1:8000/health`.
5. **Storage Mounts**:
   - `/app/data/workflow_records`: Persistent storage for proposal history (`records.json`).
   - `/app/logs`: Service runtime log directory (`cmo_service.log`).

---

## 5. Local & VM Deployment Options

### Option A: Local / Development Stack
```bash
# Build and run containers (mapped on host port 8035)
docker compose up -d --build

# Verify container status
docker compose ps

# Run health check probe on port 8035
./scripts/healthcheck.sh
```

### Option B: Production Compose Stack
```bash
# Generate production compose from template
export COMMIT_SHA=$(git rev-parse --short=7 HEAD)
sed "s|IMG_TAG|${COMMIT_SHA}|g" docker-compose.production.template.yml > docker-compose.production.yml

# Deploy production stack
docker compose -f docker-compose.production.yml up -d --remove-orphans

# Check logs
docker compose -f docker-compose.production.yml logs -f
```

---

## 6. GitHub Actions CI/CD Pipeline

The automated CI/CD pipeline (`.github/workflows/cicd.yml`) executes on every push to `main` and via `workflow_dispatch`:

1. **`validate`**:
   - Substitutes `IMG_TAG` in `docker-compose.production.template.yml` with the short commit SHA.
   - Validates compose schema using `docker compose config`.
   - Uploads deployment artifacts.

2. **`build`**:
   - Sets up Docker Buildx.
   - Authenticates against Docker Hub.
   - Builds container image and pushes tags:
     - `bhiv/cmo-agent-api:<short_sha>`
     - `bhiv/cmo-agent-api:latest`

3. **`deploy`**:
   - Creates `.env` directly from `${{ secrets.CMO_ENV_FILE }}`.
   - Bundles `deployment.tar.gz`.
   - Transports archive to target VM using `sshpass` and `scp`.
   - On the VM:
     - Extracts tarball into `~/CMO`.
     - Restores persistent `docs/RELEASE_HISTORY.md` from `/var/tmp/CMO/`.
     - Pulls image `bhiv/cmo-agent-api:<short_sha>`.
     - Launches container: `docker compose -f docker-compose.production.yml up -d --remove-orphans`.
     - Polls `/health` on port **8035** in a 12-cycle retry loop.
     - Logs deployment in `docs/RELEASE_HISTORY.md`.
     - Prunes stale images older than 7 days (`docker image prune -af --filter "until=168h"`).

4. **`rollback`**:
   - Triggered automatically if `deploy` fails.
   - Reads `docs/RELEASE_HISTORY.md` to identify the last known healthy SHA.
   - Restores compose template with previous stable SHA and redeploys.
   - Confirms port 8035 `/health` endpoint response and logs rollback status.

---

## 7. Required GitHub Repository Secrets

Configure the following secrets in **Settings > Secrets and variables > Actions**:

| Secret Key | Description | Example / Format |
|---|---|---|
| `DOCKER_USERNAME` | Docker Hub username | `bhiv` |
| `DOCKER_PASSWORD` | Docker Hub Personal Access Token | `dckr_pat_...` |
| `VM_IP` | Target VM IP address or hostname | `192.168.1.100` |
| `VM_PORT` | Target VM SSH port | `22` |
| `VM_USERNAME` | Remote VM SSH user | `ubuntu` / `azureuser` |
| `VM_PASSWORD` | Remote VM SSH password | `********` |
| `CMO_ENV_FILE` | Complete production `.env` file contents | *(Full contents of .env.production)* |

---

## 8. Verification & Smoke Testing (Port 8035)

### A. Health Probe
```bash
curl -i http://localhost:8035/health
```
**Expected Response (HTTP 200 OK):**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "path": "Path B",
  "kernel_status": "READY",
  "index_fingerprint": "a3f5b...64charSha256...",
  "persistence_status": "READY",
  "masterdb_status": "MASTERDB_CONNECTED"
}
```

### B. Policy QA Query Smoke Test
```bash
curl -X POST http://localhost:8035/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -d '{"query": "What is the maximum allowable budget allocation for any individual marketing campaign?"}'
```

### C. Proposal Intake & Governance Evaluation
```bash
curl -X POST http://localhost:8035/api/v1/proposals/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -d '{
    "proposal_id": "REQ-DEPLOY-TEST-001",
    "title": "Smoke Test Campaign",
    "proposal_text": "Allocate $10,000 to Paid Search campaign.",
    "requested_budget": 10000.0,
    "channel": "Paid Search"
  }'
```

---

## 9. Operational Scripts Guide

All scripts are located in `scripts/`:

```bash
# Make all scripts executable
chmod +x scripts/*.sh

# Deploy / Up
./scripts/deploy.sh

# Run health diagnostics on port 8035
./scripts/healthcheck.sh

# Restart services
./scripts/restart.sh

# Follow runtime logs
./scripts/logs.sh

# Stop stack
./scripts/stop.sh

# Rollback to specific or previous tag
./scripts/rollback.sh [TAG]
```
