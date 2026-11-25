"""Regression tests for Live Dashboard UI alignment, backend channel caps, and governance guards."""
from pathlib import Path
import pytest
from fastapi import HTTPException

from evidence_rag.config import REPO_ROOT
from evidence_rag.record_store import RecordStore
from evidence_rag.workflow import DecisionWorkflow
from evidence_rag.workflow_schemas import WorkflowStatus, ApprovalDecision
from evidence_rag.api.schemas import (
    ProposalEvaluateRequest,
    ProposalApprovalRequest,
    ProposalRejectionRequest,
    KnowledgeQueryRequest,
)
from evidence_rag.api.routes.proposals import (
    evaluate_proposal,
    approve_proposal,
    reject_proposal,
)
from evidence_rag.api.routes.query import query_knowledge_base
from evidence_rag.api.routes.health import health_probe
from evidence_rag.api.masterdb_client import MasterDBPersistenceAdapter
from evidence_rag.api.dependencies import verify_tantra_token
from evidence_rag.api.config import api_settings


INDEX_HTML_PATH = REPO_ROOT / "src" / "evidence_rag" / "api" / "static" / "index.html"


def test_index_html_removes_hardcoded_token_and_fixes_schema_and_controls():
    """Verify static HTML contains all required R1-R4 fixes and no hardcoded mock bearer token."""
    html = INDEX_HTML_PATH.read_text(encoding="utf-8")

    # R4: No hardcoded mock bearer token
    assert "mock-rs256-test-token" not in html

    # R1: Backend schema alignment (verified_facts + object citation formatting, not .facts)
    assert "rec.verified_facts" in html
    assert "recommendation.facts" not in html
    assert "formatCitationTag" in html

    # R2: Dynamic backend verdict, conflict state, inferences, unknowns
    assert "CONFLICT_DETECTED" in html
    assert "rec.recommended_action" in html
    assert "rec.risk_assessment" in html
    assert "rec.inferences" in html
    assert "rec.unknowns" in html

    # R3: Mute Helper Tips & Policy AI gating on corpusAllowed / aiPaused
    assert "ctrlMuteBtn" in html
    assert "toggleMuteTips" in html
    assert "if (!state.corpusAllowed)" in html
    assert "if (state.aiPaused)" in html

    # R4: Screen 3 Undo & Optional details; Screen 5 empty initial reviewer/notes
    assert 'id="btnUndoStep3"' in html
    assert 'id="inpAudience"' in html
    assert 'id="inpGoalText"' in html
    assert 'id="inpReviewer" value=""' in html
    assert '<textarea id="inpNotes" placeholder=' in html
    assert "Content-Security-Policy" in html


@pytest.fixture
def isolated_workflow(tmp_path):
    store = RecordStore(tmp_path / "records")
    wf = DecisionWorkflow(record_store=store)
    wf.ensure_index()
    return wf


def test_channel_budget_caps_enforced_across_doc_mkt_002(isolated_workflow):
    """Verify DOC-MKT-002 channel caps for Google Ads ($20k) and Content Marketing ($7.5k)."""
    search_rec = evaluate_proposal(
        ProposalEvaluateRequest(
            proposal_id="REQ-SEARCH-CAP-1",
            title="Q4 Google Search Over-Cap Test",
            proposal_text="Run Google Search Ads campaign targeting enterprise AI buyers.",
            requested_budget=25000.0,
            channel="Paid Search (Google Ads)",
        ),
        workflow=isolated_workflow,
        token="valid-token",
    )
    assert search_rec.status == WorkflowStatus.AWAITING_APPROVAL
    assert search_rec.recommendation is not None
    assert search_rec.recommendation.recommended_action == "APPROVE_WITH_CONDITIONS"
    assert any("20,000.00" in inf for inf in search_rec.recommendation.inferences)

    content_rec = evaluate_proposal(
        ProposalEvaluateRequest(
            proposal_id="REQ-CONTENT-CAP-1",
            title="Q4 Content Marketing Over-Cap Test",
            proposal_text="Produce enterprise whitepapers and case studies for Q4 pipeline.",
            requested_budget=10000.0,
            channel="Content Marketing",
        ),
        workflow=isolated_workflow,
        token="valid-token",
    )
    assert content_rec.status == WorkflowStatus.AWAITING_APPROVAL
    assert content_rec.recommendation is not None
    assert content_rec.recommendation.recommended_action == "APPROVE_WITH_CONDITIONS"
    assert any("7,500.00" in inf for inf in content_rec.recommendation.inferences)


def test_linear_tv_channel_metadata_abstains_and_logs_trace_id(isolated_workflow):
    """DEFECT-SEMANTIC-001: Linear TV in channel metadata triggers abstention with trace_id."""
    rec = evaluate_proposal(
        ProposalEvaluateRequest(
            proposal_id="REQ-LTV-META-1",
            title="Custom Broad Campaign",
            proposal_text="Run a broad awareness pilot across national media spots.",
            requested_budget=25000.0,
            channel="Linear TV Broadcasting",
        ),
        workflow=isolated_workflow,
        token="valid-token",
    )
    assert rec.status == WorkflowStatus.INSUFFICIENT_EVIDENCE
    assert rec.recommendation is None
    suf_events = [h for h in rec.history if h.get("action") == "SUFFICIENCY_FAILED"]
    assert suf_events and suf_events[0].get("trace_id") == rec.trace_id


def test_conflict_detected_blocks_approval_and_insufficient_evidence_blocks_both(isolated_workflow):
    """CONFLICT_DETECTED blocks approval (400), while INSUFFICIENT_EVIDENCE blocks both approve and reject."""
    rec = evaluate_proposal(
        ProposalEvaluateRequest(
            proposal_id="REQ-CONFLICT-GATE-1",
            title="Influencer Spend Strategy",
            proposal_text="Allocate funds for influencer partnership spend ceiling and creator endorsements.",
            requested_budget=18000.0,
            channel="Influencer & KOL Partnerships",
        ),
        workflow=isolated_workflow,
        token="valid-token",
    )
    assert rec.status == WorkflowStatus.CONFLICT_DETECTED

    with pytest.raises(HTTPException) as exc_app:
        approve_proposal(
            "REQ-CONFLICT-GATE-1",
            ProposalApprovalRequest(reviewer_identity="Pratik Bhuwad - PO"),
            workflow=isolated_workflow,
            token="valid-token",
        )
    assert exc_app.value.status_code == 400

    # INSUFFICIENT_EVIDENCE cannot be approved or rejected in RecordStore or API
    tv_rec = evaluate_proposal(
        ProposalEvaluateRequest(
            proposal_id="REQ-LTV-GATE-1",
            title="Linear TV Test",
            proposal_text="Broadcast linear television ads.",
            requested_budget=10000.0,
            channel="Linear TV Broadcasting",
        ),
        workflow=isolated_workflow,
        token="valid-token",
    )
    assert tv_rec.status == WorkflowStatus.INSUFFICIENT_EVIDENCE

    with pytest.raises(HTTPException) as exc_tv_rej:
        reject_proposal(
            "REQ-LTV-GATE-1",
            ProposalRejectionRequest(
                reviewer_identity="Pratik Bhuwad - PO",
                decision_notes="Attempting reject on insufficient evidence.",
            ),
            workflow=isolated_workflow,
            token="valid-token",
        )
    assert exc_tv_rej.value.status_code == 400

    with pytest.raises(ValueError, match="Cannot record decision"):
        isolated_workflow.record_store.record_decision(
            "REQ-LTV-GATE-1",
            ApprovalDecision(
                request_id="REQ-LTV-GATE-1",
                decision="REJECTED",
                reviewer="Pratik Bhuwad - PO",
                decision_notes="Direct store rejection attempt on insufficient evidence",
            ),
        )


def test_auth_and_direct_route_flow(isolated_workflow):
    """Verify Bearer auth fail-closed checks and direct health/query/proposal route flow."""
    with pytest.raises(HTTPException) as exc_missing:
        verify_tantra_token(None)
    assert exc_missing.value.status_code == 401

    orig_strict = api_settings.auth_strict_rs256
    try:
        api_settings.auth_strict_rs256 = True
        with pytest.raises(HTTPException) as exc_mock:
            verify_tantra_token("Bearer mock-rs256-test-token")
        assert exc_mock.value.status_code == 401
    finally:
        api_settings.auth_strict_rs256 = orig_strict

    adapter = MasterDBPersistenceAdapter(base_url="http://127.0.0.1:9999", record_store=isolated_workflow.record_store)
    h = health_probe(isolated_workflow, adapter)
    assert h.status == "ok"

    q = query_knowledge_base(
        KnowledgeQueryRequest(query="What is the maximum allowable budget ceiling?"),
        workflow=isolated_workflow,
        token="valid-token",
    )
    assert q.trace_id.startswith("TRC-QRY-")
    assert len(q.answer) > 10
