"""Regression tests for DQ-005 3-tier influencer budget conflict boundaries."""
import pytest
from evidence_rag.workflow import DecisionWorkflow
from evidence_rag.workflow_schemas import WorkflowRequest, WorkflowStatus
from evidence_rag.record_store import RecordStore


def _make_influencer_request(req_id: str, budget: float) -> WorkflowRequest:
    return WorkflowRequest(
        request_id=req_id,
        title="Q4 Influencer & KOL Partnership Campaign",
        proposal_text="Allocate budget for influencer partnership spend ceiling and creator endorsements.",
        department="Marketing",
        requested_budget=budget,
        submitted_by="hariom_dq005_test",
        metadata={"channel": "Influencer and KOL Partnerships"}
    )


def test_dq005_influencer_tier1_at_10000_proceeds_without_conflict_halt(tmp_path):
    """Spend <= $10,000 satisfies both DOC-MKT-004 ($10k) and DOC-MKT-002 ($25k) caps."""
    wf = DecisionWorkflow(
        config_path="configs/marketing_workflow.yaml",
        record_store=RecordStore(tmp_path / "records"),
    )
    rec = wf.evaluate_proposal(_make_influencer_request("DQ005-10000", 10000.00))

    assert rec.status == WorkflowStatus.AWAITING_APPROVAL
    assert rec.recommendation is not None
    assert rec.recommendation.recommended_action == "APPROVE"
    cited_docs = {c.document_id for c in rec.citations}
    assert "DOC-MKT-002" in cited_docs or "DOC-MKT-004" in cited_docs


def test_dq005_influencer_tier2_10000_01_and_25000_emit_conflict_detected(tmp_path):
    """Spend > $10,000 and <= $25,000 must emit CONFLICT_DETECTED citing both DOC-MKT-002 and DOC-MKT-004."""
    wf = DecisionWorkflow(
        config_path="configs/marketing_workflow.yaml",
        record_store=RecordStore(tmp_path / "records"),
    )
    for req_id, budget in [("DQ005-10000-01", 10000.01), ("DQ005-25000", 25000.00)]:
        rec = wf.evaluate_proposal(_make_influencer_request(req_id, budget))
        assert rec.status == WorkflowStatus.CONFLICT_DETECTED
        assert rec.conflict is not None
        assert "DOC-MKT-002" in rec.conflict.conflicting_sources
        assert "DOC-MKT-004" in rec.conflict.conflicting_sources
        cited_docs = {c.document_id for c in rec.citations}
        assert "DOC-MKT-002" in cited_docs
        assert "DOC-MKT-004" in cited_docs
        assert rec.approval is None


def test_dq005_influencer_tier3_25000_01_is_hard_violation(tmp_path):
    """Spend > $25,000 is an immediate hard violation recommending REJECT."""
    wf = DecisionWorkflow(
        config_path="configs/marketing_workflow.yaml",
        record_store=RecordStore(tmp_path / "records"),
    )
    rec = wf.evaluate_proposal(_make_influencer_request("DQ005-25000-01", 25000.01))

    assert rec.status == WorkflowStatus.AWAITING_APPROVAL
    assert rec.recommendation is not None
    assert rec.recommendation.recommended_action == "REJECT"
    assert "Hard Policy Violation" in rec.recommendation.risk_assessment
    assert rec.conflict is not None
    assert "DOC-MKT-002" in rec.conflict.conflicting_sources
    assert "DOC-MKT-004" in rec.conflict.conflicting_sources


def test_dq005_subcent_precision_preserved_in_outputs(tmp_path):
    """Sub-cent boundary value $25,000.001 must not be rounded to $25,000.00 in decision text."""
    wf = DecisionWorkflow(
        config_path="configs/marketing_workflow.yaml",
        record_store=RecordStore(tmp_path / "records"),
    )
    rec = wf.evaluate_proposal(_make_influencer_request("DQ005-25000-001", 25000.001))

    assert rec.status == WorkflowStatus.AWAITING_APPROVAL
    assert rec.recommendation.recommended_action == "REJECT"
    assert "$25,000.001" in rec.recommendation.risk_assessment
    assert any("$25,000.001" in inf for inf in rec.recommendation.inferences)
