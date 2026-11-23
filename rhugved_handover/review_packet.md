# CMO Agent V2 — Path B Technical Execution & QA Review Packet

**Document Identifier:** `EVID-CMO-REVIEW-PACKET-001`  
**Execution Date:** 21 November 2026  
**Subject:** Technical Verification & Reproduction Packet for Path B REST Microservice & MASTERDB Integration  
**Target Verifier:** **Samsoorya Rajakumar** (QA & Test Automation Lead)  
**Authors:** Pratik Bhuwad (Acting Backend Lead) on behalf of Rhugved (Original Assignee)  
**Repository Branch:** `main`  
**Commit Baseline:** All working tree changes verified and staged  

---

## 1. Quick Verification Runbook for Tester

### 1.1 Automated Test Suite Execution
To verify that all 152 automated tests pass with 100% green integrity across all 29 test suites:

```powershell
# Navigate to the repository root
cd c:\Pratik_Bhuwad\CMO_Agent\evidence-grounded-rag-main

# Activate Python 3.11 virtual environment
..\.venv\Scripts\Activate.ps1

# Execute the complete automated test suite
pytest tests -v
```

**Expected Baseline Result:**
```text
======================= 154 passed, 1 warning in 10.53s =======================
```
*Note: Tracked files (`logs/rag_system.log`, `records.json`) remain 100% untouched after test execution.*

---

### 1.2 Local Service Startup (Standalone)
To start the Path B FastAPI microservice locally:

```powershell
# Set environment configuration
$env:API_HOST = "0.0.0.0"
$env:API_PORT = "8000"
$env:MASTERDB_URL = "http://127.0.0.1:8000"
$env:API_AUTH_ENABLED = "true"

# Start the uvicorn ASGI server
uvicorn evidence_rag.api.app:app --host 0.0.0.0 --port 8000 --reload
```

---

### 1.3 Containerized Execution via Docker Compose
To run the containerized microservice alongside the local MASTERDB capability testbed:

```bash
# Validate compose configuration
docker-compose config

# Build and start services in the background
docker-compose up -d --build

# Inspect service logs
docker-compose logs -f cmo-api
```

---

## 2. API Endpoint Reproduction Recipes (Curl Transcripts)

All endpoints require a Bearer token in the `Authorization` header. In non-production testing, `Authorization: Bearer mock-rs256-test-token` is authorized.

### Endpoint 1: Health & Kernel Readiness Probe
```bash
curl -X GET http://127.0.0.1:8000/health
```

**Expected HTTP Response (200 OK):**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "path": "Path B",
  "kernel_status": "READY",
  "index_fingerprint": "a9e80d2dc287629f9dd5677aa8a9f0f5abe1ce748073c1c41d99978ac1bab825",
  "persistence_status": "READY",
  "masterdb_status": "LOCAL_STORE_FALLBACK",
  "timestamp": "2026-11-21T05:24:19.857720+00:00"
}
```

---

### Endpoint 2: Knowledge QA Policy Query
```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the maximum allowed budget ceiling for influencer marketing campaigns?"
  }'
```

**Expected HTTP Response (200 OK):**
```json
{
  "query": "What is the maximum allowed budget ceiling for influencer marketing campaigns?",
  "answer": "According to corporate financial policies, influencer partnerships are strictly capped at $25,000 for standard tier campaigns [DOC-MKT-002].",
  "confidence": 0.88,
  "citations": [
    {
      "document_id": "DOC-MKT-002",
      "chunk_id": "DOC-MKT-002-C001",
      "quote": "Influencer marketing expenditures cannot exceed the $25,000 active media spend ceiling without CMO written sign-off.",
      "is_valid": true
    }
  ],
  "trace_id": "TRC-QRY-20261121-4A82F10B",
  "timestamp": "2026-11-21T05:30:11.120000+00:00"
}
```

---

### Endpoint 3: Canonical $30,000 LinkedIn Proposal Intake (Mandatory Hard Stop)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/proposals/evaluate \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": "REQ-MKT-2026-LI-01",
    "title": "Q4 LinkedIn Sponsored Content Executive Acquisition",
    "proposal_text": "Deploy sponsored content campaign on LinkedIn targeting enterprise decision makers. Total proposed media spend is $30,000. Expected CTR is 2.2% with estimated CAC of $35.00.",
    "requested_budget": 30000.0,
    "channel": "LinkedIn",
    "submitted_by": "analyst"
  }'
```

**Expected HTTP Response (200 OK):**
```json
{
  "request_id": "REQ-MKT-2026-LI-01",
  "status": "AWAITING_APPROVAL",
  "trace_id": "TRC-20261121-6C7BDA95",
  "approval": null,
  "recommendation": {
    "recommended_action": "APPROVE_WITH_CONDITIONS",
    "risk_assessment": "Moderate Financial Risk: Allocation exceeds recommended active media spend buffer.",
    "inferences": [
      "Requested budget of $30,000.00 exceeds the active media spend buffer of $25,000.00 by $5,000.00 [DOC-MKT-002]."
    ]
  },
  "history": [
    {"action": "REQUEST_SUBMITTED", "trace_id": "TRC-20261121-6C7BDA95"},
    {"action": "EVIDENCE_RETRIEVED", "chunk_count": 4},
    {"action": "RECOMMENDATION_SYNTHESIZED", "action_proposed": "APPROVE_WITH_CONDITIONS"},
    {"action": "AWAITING_HUMAN_APPROVAL", "message": "Recommendation ready for human review. System cannot execute without sign-off."}
  ]
}
```
**CRITICAL GOVERNANCE VERIFICATION:**  
- Status is **`AWAITING_APPROVAL`**.
- Field `approval` is **`null`**.
- Zero external ad-network spend calls or autonomous execution occurred.

---

### Endpoint 4: Semantic Abstention on Linear TV (`DEFECT-SEMANTIC-001`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/proposals/evaluate \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": "REQ-MKT-TEST-LTV-01",
    "title": "National Linear TV Broadcaster Ad Pilot",
    "proposal_text": "Allocate $20,000 to Linear TV broadcasting advertising across primetime networks.",
    "requested_budget": 20000.0,
    "channel": "Linear TV"
  }'
```

**Expected HTTP Response (200 OK):**
```json
{
  "request_id": "REQ-MKT-TEST-LTV-01",
  "status": "INSUFFICIENT_EVIDENCE",
  "approval": null,
  "history": [
    {
      "action": "SUFFICIENCY_FAILED",
      "reason": "Insufficient evidence: Corporate knowledge base contains no performance benchmarks, conversion data, or audience research for Linear TV broadcasting [DEFECT-SEMANTIC-001 / DOC-MKT-003]."
    }
  ]
}
```

---

### Endpoint 5: Placeholder Reviewer Identity Rejection (`QA-001`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/proposals/REQ-MKT-2026-LI-01/approve \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_identity": "prof_evaluator",
    "decision_notes": "Looks acceptable to me."
  }'
```

**Expected HTTP Response (422 Unprocessable Content):**
```json
{
  "detail": "Default reviewer placeholder 'prof_evaluator' is rejected. An explicit authorized reviewer (e.g. 'Pratik Bhuwad - CMO Product Owner') is required."
}
```

---

### Endpoint 6: Valid Human Reviewer Approval & Audit Trail
```bash
curl -X POST http://127.0.0.1:8000/api/v1/proposals/REQ-MKT-2026-LI-01/approve \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_identity": "Pratik Bhuwad - CMO Product Owner",
    "decision_notes": "Approved with condition that spend is capped at $25,000 for initial 2-week flight."
  }'
```

**Expected HTTP Response (200 OK):**
```json
{
  "request_id": "REQ-MKT-2026-LI-01",
  "status": "APPROVED",
  "trace_id": "TRC-20261121-6C7BDA95",
  "approval": {
    "request_id": "REQ-MKT-2026-LI-01",
    "decision": "APPROVED",
    "reviewer": "Pratik Bhuwad - CMO Product Owner",
    "decision_notes": "Approved with condition that spend is capped at $25,000 for initial 2-week flight."
  },
  "history": [
    {
      "action": "HUMAN_APPROVED",
      "trace_id": "TRC-20261121-6C7BDA95",
      "reviewer": "Pratik Bhuwad - CMO Product Owner",
      "decision_notes": "Approved with condition that spend is capped at $25,000 for initial 2-week flight."
    }
  ]
}
```

---

### Endpoint 7: Duplicate Decision Prevention (`DEFECT-003`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/proposals/REQ-MKT-2026-LI-01/approve \
  -H "Authorization: Bearer mock-rs256-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_identity": "Pratik Bhuwad - CMO Product Owner"
  }'
```

**Expected HTTP Response (409 Conflict):**
```json
{
  "detail": "Proposal 'REQ-MKT-2026-LI-01' has already been finalized with status 'APPROVED'."
}
```

---

### Endpoint 8: Deterministic Replay
```bash
curl -X POST http://127.0.0.1:8000/api/v1/proposals/REQ-MKT-2026-LI-01/replay \
  -H "Authorization: Bearer mock-rs256-test-token"
```

**Expected HTTP Response (200 OK):** Returns re-evaluated `WorkflowRecord` preserving deterministic recommendations.

---

### Endpoint 9: Proposal Audit Retrieval
```bash
curl -X GET http://127.0.0.1:8000/api/v1/proposals/REQ-MKT-2026-LI-01 \
  -H "Authorization: Bearer mock-rs256-test-token"
```

**Expected HTTP Response (200 OK):** Returns full audit envelope for `REQ-MKT-2026-LI-01`.

---

## 3. QA Acceptance Sign-Off Checklist for Tester (Samsoorya Rajakumar)

| # | Acceptance Criterion | Verification Command / Target | Pass / Fail |
| :-: | :--- | :--- | :-: |
| 1 | **Full Pytest Suite (152 tests)** | `pytest tests -v` (152 passed, 0 failures, 0 errors) | [ ] PASS |
| 2 | **Path Reproducibility (`DEF-REPRO-001`)** | `pytest tests/regression/test_environment_reproducibility.py` | [ ] PASS |
| 3 | **Reviewer Gate (`QA-001`)** | Reject `prof_evaluator`, `anonymous` with HTTP 422 | [ ] PASS |
| 4 | **Illegal State Rejection (`QA-002`)** | Approve on `INSUFFICIENT_EVIDENCE` fails with HTTP 400 | [ ] PASS |
| 5 | **Trace Correlation (`QA-003`)** | `trace_id` recorded on `HUMAN_APPROVED` event | [ ] PASS |
| 6 | **Fail-Closed Store (`QA-004`)** | Corrupt `records.json` raises `IOError` on save | [ ] PASS |
| 7 | **Zero Test Pollution (`QA-012`)** | `git status` shows 0 diff in `logs/` or `records.json` | [ ] PASS |
| 8 | **Duplicate Conflict (`DEFECT-003`)** | Re-approving returns HTTP 409 Conflict | [ ] PASS |
| 9 | **Linear TV Abstention** | Linear TV proposal status is `INSUFFICIENT_EVIDENCE` | [ ] PASS |
| 10 | **Mandatory Hard Gate** | $30,000 LinkedIn proposal halts at `AWAITING_APPROVAL` with `approval: null` | [ ] PASS |
| 11 | **MASTERDB Offline Resilience** | Microservice boots and functions when port 8000 is down | [ ] PASS |
| 12 | **Containerization Assets** | `docker-compose config` parses cleanly with 0 errors | [ ] PASS |
