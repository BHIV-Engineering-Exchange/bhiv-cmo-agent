"""Functional integration test suite for CMO Agent V2 Executive Command Center.

Covers:
- Group A: Executive Command Center (/api/v1/dashboard/kpis, strategy-progress, campaign-portfolio, budget-summary, forecast-and-risks)
- Group B: AI Recommendations & 5-Gate Governance (/api/v1/governance/recommendations, decision-queue, sign-off)
- Group C: Omni-Search & Executive Assistant (/api/v1/cmo/chat)
- Authentication boundaries and state machine guarantees
"""
import pytest
from fastapi.testclient import TestClient

from evidence_rag.api.app import create_app
from evidence_rag.api.cmo_store import get_cmo_store
from evidence_rag.api.cmo_schemas import GovernanceGate, DecisionStatus


@pytest.fixture(scope="module")
def api_client(tmp_path_factory):
    """Create isolated TestClient with dedicated temporary storage for records and governance queue."""
    temp_dir = tmp_path_factory.mktemp("cmo_v2_records")
    gov_dir = tmp_path_factory.mktemp("cmo_v2_governance")

    # Override persistence adapters to use temp directories
    from evidence_rag.record_store import RecordStore
    from evidence_rag.api import dependencies, cmo_store
    from evidence_rag.api.masterdb_client import MasterDBPersistenceAdapter
    from evidence_rag.workflow import DecisionWorkflow

    temp_store = RecordStore(storage_dir=temp_dir)
    adapter = MasterDBPersistenceAdapter(
        base_url="http://127.0.0.1:8000",
        record_store=temp_store
    )
    dependencies._persistence_adapter = adapter

    wf = DecisionWorkflow(record_store=temp_store)
    wf.ensure_index()
    dependencies._workflow_instance = wf

    # Override CMOStore storage directory
    test_cmo_store = cmo_store.CMOStore(data_dir=gov_dir)
    cmo_store._cmo_store_instance = test_cmo_store

    app = create_app()

    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Standard Bearer token authorization header."""
    return {"Authorization": "Bearer mock-rs256-test-token"}


# =============================================================================
# 1. Group A: Executive Command Center Tests (/api/v1/dashboard)
# =============================================================================

def test_dashboard_kpis_endpoint(api_client, auth_headers):
    """Verify GET /api/v1/dashboard/kpis returns executive metrics with INR currency."""
    for path in ("/dashboard/kpis", "/api/v1/dashboard/kpis"):
        resp = api_client.get(path, headers=auth_headers)
        assert resp.status_code == 200, f"Failed on path {path}: {resp.text}"
        data = resp.json()

        assert data["period"] == "Q4 FY26"
        assert data["currency"] == "INR"
        metrics = data["metrics"]

        # Validate marketing contribution revenue
        rev = metrics["marketing_contribution_revenue"]
        assert rev["value"] == 284000000
        assert rev["formatted"] == "₹28.4 Cr"
        assert rev["change_qoq_pct"] == 15.0
        assert rev["trend"] == "up"

        # Validate qualified pipeline
        pipe = metrics["qualified_pipeline"]
        assert pipe["value"] == 967000000
        assert pipe["formatted"] == "₹96.7 Cr"
        assert pipe["change_pct"] == 24.0
        assert pipe["trend"] == "up"

        # Validate brand health
        bh = metrics["brand_health_index"]
        assert bh["score"] == 82
        assert bh["max_score"] == 100
        assert bh["change_pts"] == 6

        # Validate CAC
        cac = metrics["cac"]
        assert cac["value"] == 14200
        assert cac["formatted"] == "₹14,200"
        assert cac["change_pct"] == -12.0
        assert cac["trend"] == "positive_reduction"

        # Validate marketing ROI
        roi = metrics["marketing_roi"]
        assert roi["multiple"] == 4.8
        assert roi["change_pts"] == 0.9

        # Validate customer NPS
        nps = metrics["customer_nps"]
        assert nps["score"] == 56
        assert nps["change_pts"] == 8


def test_strategy_progress_endpoint(api_client, auth_headers):
    """Verify GET /api/v1/dashboard/strategy-progress returns OKRs and initiatives."""
    for path in ("/dashboard/strategy-progress", "/api/v1/dashboard/strategy-progress", "/api/v1/strategy/okrs"):
        resp = api_client.get(path, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["overall_progress_pct"] == 76
        assert data["status"] == "ON_TRACK"
        initiatives = data["initiatives"]
        assert len(initiatives) == 5

        names = [init["name"] for init in initiatives]
        assert "Market expansion (India - Phase 1)" in names
        assert "Brand repositioning rollout" in names
        assert "Demand generation scale-up" in names
        assert "Product GTM - AI Suite" in names
        assert "Customer retention program" in names


def test_campaign_portfolio_endpoint(api_client, auth_headers):
    """Verify GET /api/v1/dashboard/campaign-portfolio returns category distributions."""
    for path in ("/dashboard/campaign-portfolio", "/api/v1/dashboard/campaign-portfolio", "/api/v1/campaigns"):
        resp = api_client.get(path, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["active_campaigns_total"] == 12
        distribution = data["distribution"]
        assert len(distribution) == 6

        total_pct = sum(d["percentage"] for d in distribution)
        assert total_pct == 100
        total_count = sum(d["count"] for d in distribution)
        assert total_count == 12


def test_budget_summary_endpoint(api_client, auth_headers):
    """Verify GET /api/v1/dashboard/budget-summary returns budget commitments, spend, and ROI."""
    for path in ("/dashboard/budget-summary", "/api/v1/dashboard/budget-summary", "/api/v1/budget/summary"):
        resp = api_client.get(path, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_budget"] == 60000000.0
        assert data["formatted_total"] == "₹6.0 Cr"
        assert data["committed"] == 42000000.0
        assert data["committed_pct"] == 70
        assert data["spent"] == 28000000.0
        assert data["spent_pct"] == 47
        assert data["remaining"] == 18000000.0
        assert data["forecast_roi"] == "5.1x"


def test_forecast_and_risks_endpoint(api_client, auth_headers):
    """Verify GET /api/v1/dashboard/forecast-and-risks returns projections and watchlist."""
    for path in ("/dashboard/forecast-and-risks", "/api/v1/dashboard/forecast-and-risks", "/api/v1/analytics/forecast"):
        resp = api_client.get(path, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        forecast = data["monthly_forecast"]
        assert len(forecast) == 5
        months = [f["month"] for f in forecast]
        assert months == ["Nov", "Dec", "Jan", "Feb", "Mar"]

        risks = data["risks"]
        assert len(risks) == 3
        risk_ids = [r["id"] for r in risks]
        assert "RSK-01" in risk_ids
        assert "RSK-02" in risk_ids
        assert "RSK-03" in risk_ids

        cap = data["team_capacity"]
        assert cap["capacity_pct"] == 82
        assert cap["team_count"] == 14
        assert cap["agencies_count"] == 3
        assert cap["active_projects"] == 27


# =============================================================================
# 2. Group B: AI Recommendations & 5-Gate Governance Tests
# =============================================================================

def test_ai_recommendations_endpoint(api_client, auth_headers):
    """Verify GET /api/v1/governance/recommendations returns prioritized recommendations."""
    for path in ("/governance/recommendations", "/api/v1/governance/recommendations", "/api/v1/recommendations"):
        resp = api_client.get(path, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        recs = data["recommendations"]
        assert len(recs) == 3
        assert recs[0]["id"] == "REC-001"
        assert recs[0]["priority"] == 1
        assert "LinkedIn" in recs[0]["title"]
        assert recs[0]["confidence_score"] == 0.87
        assert recs[0]["action_type"] == "CAMPAIGN_SCALE"

        assert recs[1]["id"] == "REC-002"
        assert recs[1]["action_type"] == "GTM_APPROVAL"

        assert recs[2]["id"] == "REC-003"
        assert recs[2]["action_type"] == "BUDGET_REALLOCATION"


def test_decision_queue_listing(api_client, auth_headers):
    """Verify GET /api/v1/governance/decision-queue returns pending items across the 5 gates."""
    resp = api_client.get("/api/v1/governance/decision-queue", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["pending_count"] >= 4
    queue = data["queue"]
    dec_ids = [item["decision_id"] for item in queue]
    assert "DEC-BUD-001" in dec_ids
    assert "DEC-GTM-002" in dec_ids
    assert "DEC-VND-003" in dec_ids
    assert "DEC-BRD-004" in dec_ids

    # Validate gate categories
    gates = [item["gate"] for item in queue]
    assert GovernanceGate.BUDGET_GATE.value in gates
    assert GovernanceGate.STRATEGY_GATE.value in gates
    assert GovernanceGate.VENDOR_CONTRACT_GATE.value in gates
    assert GovernanceGate.BRAND_LEGAL_GATE.value in gates


def test_gate_decision_approval_lifecycle(api_client, auth_headers):
    """Verify POST /api/v1/governance/decisions/{decision_id}/sign-off approves a pending gate decision."""
    payload = {
        "action": "APPROVED",
        "signer_identity": "cmo_user@biqos.com",
        "signer_role": "Chief Marketing Officer",
        "notes": "Approved following quarterly target alignment review."
    }

    resp = api_client.post(
        "/api/v1/governance/decisions/DEC-BUD-001/sign-off",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision_id"] == "DEC-BUD-001"
    assert data["status"] == DecisionStatus.APPROVED.value
    assert data["action"] == "APPROVED"
    assert data["signer_identity"] == "cmo_user@biqos.com"
    assert data["gate"] == GovernanceGate.BUDGET_GATE.value
    assert "signed_at" in data

    # Verify pending count in queue decreased
    queue_resp = api_client.get("/api/v1/governance/decision-queue", headers=auth_headers)
    queue_data = queue_resp.json()
    assert queue_data["pending_count"] == 3


def test_duplicate_sign_off_rejected_with_409(api_client, auth_headers):
    """Verify attempting to re-approve an already finalized decision is rejected with 409 Conflict."""
    payload = {
        "action": "APPROVED",
        "signer_identity": "cmo_user@biqos.com",
        "signer_role": "Chief Marketing Officer",
        "notes": "Second attempt to sign already finalized decision."
    }

    resp = api_client.post(
        "/api/v1/governance/decisions/DEC-BUD-001/sign-off",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 409
    data = resp.json()
    assert "already been finalized" in data["detail"].lower()


def test_gate_decision_rejection_lifecycle(api_client, auth_headers):
    """Verify rejecting a gate decision updates status to REJECTED."""
    payload = {
        "action": "REJECTED",
        "signer_identity": "gtm_auditor@biqos.com",
        "signer_role": "Chief Marketing Officer",
        "notes": "Rejected due to dependency on Phase 2 completion."
    }

    resp = api_client.post(
        "/api/v1/governance/decisions/DEC-GTM-002/sign-off",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == DecisionStatus.REJECTED.value
    assert data["action"] == "REJECTED"


def test_sign_off_rejects_placeholder_identity(api_client, auth_headers):
    """Verify placeholder identities like 'prof_evaluator' are rejected."""
    payload = {
        "action": "APPROVED",
        "signer_identity": "prof_evaluator",
        "signer_role": "Chief Marketing Officer",
        "notes": "Attempt with invalid placeholder."
    }

    resp = api_client.post(
        "/api/v1/governance/decisions/DEC-VND-003/sign-off",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 400
    data = resp.json()
    assert "placeholder" in data["detail"].lower()


def test_sign_off_nonexistent_decision_returns_404(api_client, auth_headers):
    """Verify signing off a non-existent decision returns 404 Not Found."""
    payload = {
        "action": "APPROVED",
        "signer_identity": "cmo_user@biqos.com",
        "signer_role": "Chief Marketing Officer",
        "notes": "Non-existent item."
    }

    resp = api_client.post(
        "/api/v1/governance/decisions/DEC-NONEXISTENT-999/sign-off",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 404


# =============================================================================
# 3. Group C: Omni-Search & Executive Assistant Tests (/api/v1/cmo/chat)
# =============================================================================

def test_cmo_chat_pipeline_and_risks_query(api_client, auth_headers):
    """Verify POST /api/v1/cmo/chat returns live metric lookups and risk grounding."""
    payload = {
        "query": "What is our qualified pipeline for Q4 and what are our biggest risks?",
        "include_metrics": True,
        "include_citations": True
    }

    resp = api_client.post("/api/v1/cmo/chat", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "₹96.7 Cr" in data["answer"]
    assert "risk" in data["answer"].lower()

    # Grounded sources should include both ERP feed and risk register
    sources = [s["source"] for s in data["grounded_sources"]]
    assert "INTERNAL_ERP_PIPELINE_FEED" in sources
    assert "DOC-MKT-RISK-003" in sources

    # Suggested actions
    assert len(data["suggested_actions"]) > 0


def test_cmo_chat_budget_and_cac_query(api_client, auth_headers):
    """Verify POST /api/v1/cmo/chat returns budget spend and CAC metrics."""
    payload = {
        "query": "What is our marketing budget spend and customer acquisition cost?",
        "include_metrics": True,
        "include_citations": True
    }

    resp = api_client.post("/api/v1/cmo/chat", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "₹6.0 Cr" in data["answer"]
    assert "₹14,200" in data["answer"]

    sources = [s["source"] for s in data["grounded_sources"]]
    assert "INTERNAL_FINANCE_BUDGET_STORE" in sources
    assert "INTERNAL_MARKETING_ANALYTICS_CAC" in sources


def test_cmo_chat_policy_rag_fallback(api_client, auth_headers):
    """Verify POST /api/v1/cmo/chat falls back cleanly to knowledge base RAG for policy questions."""
    payload = {
        "query": "What is our corporate policy regarding Linear TV broadcaster advertising?",
        "include_metrics": True,
        "include_citations": True
    }

    resp = api_client.post("/api/v1/cmo/chat", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["answer"]) > 15
    assert len(data["grounded_sources"]) > 0


# =============================================================================
# 4. Authentication Enforcement Tests
# =============================================================================

def test_unauthenticated_requests_rejected(api_client):
    """Verify all new endpoints enforce authentication when auth is enabled."""
    endpoints = [
        ("GET", "/api/v1/dashboard/kpis"),
        ("GET", "/api/v1/dashboard/strategy-progress"),
        ("GET", "/api/v1/dashboard/campaign-portfolio"),
        ("GET", "/api/v1/dashboard/budget-summary"),
        ("GET", "/api/v1/dashboard/forecast-and-risks"),
        ("GET", "/api/v1/governance/recommendations"),
        ("GET", "/api/v1/governance/decision-queue"),
        ("POST", "/api/v1/cmo/chat"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = api_client.get(path)
        else:
            resp = api_client.post(path, json={"query": "test query"})
        assert resp.status_code == 401, f"Expected 401 for {method} {path}, got {resp.status_code}"
