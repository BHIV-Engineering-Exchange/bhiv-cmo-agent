"""V4 Adversarial Regression Tests for ADV-001 through ADV-005."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from evidence_rag.evidence import CitationValidator
from evidence_rag.schemas import Chunk, RetrievedChunk, Citation
from evidence_rag.workflow import DecisionWorkflow
from evidence_rag.workflow_schemas import WorkflowRequest, WorkflowStatus
from evidence_rag.record_store import RecordStore


def _wf(tmp_path) -> DecisionWorkflow:
    return DecisionWorkflow(
        config_path="configs/marketing_workflow.yaml",
        record_store=RecordStore(tmp_path / "records"),
    )


def _inf_req(req_id: str, budget) -> WorkflowRequest:
    return WorkflowRequest(
        request_id=req_id,
        title="Q4 Influencer & KOL Partnership Campaign",
        proposal_text="Allocate budget for influencer partnership spend ceiling and creator endorsements.",
        department="Marketing",
        requested_budget=budget,
        metadata={"channel": "Influencer and KOL Partnerships"},
    )


# ---------------------------------------------------------------------------
# ADV-001: Non-finite & invalid budget validation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad_budget", [float("nan"), float("inf"), float("-inf"), -50.0])
def test_adv001_rejects_non_finite_and_negative_budgets(tmp_path, bad_budget):
    wf = _wf(tmp_path)
    rec = wf.evaluate_proposal(_inf_req("ADV001-BAD", bad_budget))
    assert rec.status == WorkflowStatus.INVALID_REQUEST
    assert rec.recommendation is None


def test_adv001_string_and_null_budgets(tmp_path):
    wf = _wf(tmp_path)
    # Valid numeric string coerced by Pydantic
    rec_str = wf.evaluate_proposal(_inf_req("ADV001-STR", "18000"))
    assert rec_str.status == WorkflowStatus.CONFLICT_DETECTED

    # Malformed string rejected at Pydantic schema boundary
    with pytest.raises(ValidationError):
        _inf_req("ADV001-MAL", "not_a_number")

    # Missing / None budget routes safely to REVIEW
    rec_none = wf.evaluate_proposal(_inf_req("ADV001-NONE", None))
    assert rec_none.status in (WorkflowStatus.AWAITING_APPROVAL, WorkflowStatus.CONFLICT_DETECTED)


# ---------------------------------------------------------------------------
# ADV-002: Citation negation / polarity validation
# ---------------------------------------------------------------------------
def _pos_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id="DOC-MKT-002-C005",
            document_id="DOC-MKT-002",
            chunk_index=4,
            text=(
                "No corporate spend may exceed $50,000.\n"
                "- **Paid Social (LinkedIn Ads):** Capped at a maximum allocation of $15,000."
            ),
        ),
        score=0.9,
        rank=1,
        raw_similarity=0.9,
    )


def _neg_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id="DOC-MKT-003-C005",
            document_id="DOC-MKT-003",
            chunk_index=4,
            text="No corporate performance data exists for linear television broadcasting.",
        ),
        score=0.9,
        rank=1,
        raw_similarity=0.9,
    )


def test_adv002_polarity_matching_and_inversions():
    cv = CitationValidator()
    pos_rc = _pos_chunk()
    pos_quote = "- **Paid Social (LinkedIn Ads):** Capped at a maximum allocation of $15,000."

    # 1. Positive claim + positive evidence -> valid
    assert cv.validate_claim_citation(
        "Paid Social (LinkedIn Ads) is capped at a maximum allocation of $15,000.",
        Citation(document_id="DOC-MKT-002", chunk_id="DOC-MKT-002-C005", quote=pos_quote),
        [pos_rc],
    ).is_valid is True

    # 2. Negative claims + positive evidence -> rejected
    for neg_stmt in [
        "Paid Social (LinkedIn Ads) is NOT capped at a maximum allocation of $15,000.",
        "Paid Social (LinkedIn Ads) has no maximum allocation cap of $15,000.",
        "Paid Social (LinkedIn Ads) is never capped at $15,000.",
        "Paid Social (LinkedIn Ads) isn't capped at $15,000.",
        "Paid Social (LinkedIn Ads) doesn't have a cap of $15,000.",
        "Paid Social (LinkedIn Ads) cannot be capped at $15,000.",
        "Paid Social (LinkedIn Ads) operates without a cap of $15,000.",
        "Paid Social (LinkedIn Ads) has an uncapped allocation of $15,000.",
    ]:
        res = cv.validate_claim_citation(
            neg_stmt,
            Citation(document_id="DOC-MKT-002", chunk_id="DOC-MKT-002-C005", quote=pos_quote),
            [pos_rc],
        )
        assert res.is_valid is False, f"Should reject negated claim: {neg_stmt}"

    # 3. Positive claim + negative evidence -> rejected
    neg_rc = _neg_chunk()
    neg_quote = "No corporate performance data exists for linear television broadcasting."
    assert cv.validate_claim_citation(
        "Corporate performance data exists for linear television broadcasting.",
        Citation(document_id="DOC-MKT-003", chunk_id="DOC-MKT-003-C005", quote=neg_quote),
        [neg_rc],
    ).is_valid is False

    # 4. Matching negative claim + negative evidence -> valid
    assert cv.validate_claim_citation(
        "No corporate performance data exists for linear television broadcasting.",
        Citation(document_id="DOC-MKT-003", chunk_id="DOC-MKT-003-C005", quote=neg_quote),
        [neg_rc],
    ).is_valid is True

    # 5. Contradictory numerical values -> rejected
    assert cv.validate_claim_citation(
        "Paid Social (LinkedIn Ads) is capped at a maximum allocation of $30,000.",
        Citation(document_id="DOC-MKT-002", chunk_id="DOC-MKT-002-C005", quote=pos_quote),
        [pos_rc],
    ).is_valid is False

    # 6. Genuine paraphrase -> valid
    assert cv.validate_claim_citation(
        "LinkedIn Ads Paid Social maximum allocation is $15,000.",
        Citation(document_id="DOC-MKT-002", chunk_id="DOC-MKT-002-C005", quote=pos_quote),
        [pos_rc],
    ).is_valid is True

    # 7. Fabricated quotation -> rejected
    assert cv.validate_claim_citation(
        "Paid Social (LinkedIn Ads) is capped at $15,000.",
        Citation(document_id="DOC-MKT-002", chunk_id="DOC-MKT-002-C005", quote="Fabricated quote"),
        [pos_rc],
    ).is_valid is False

    # 8. Negation in unrelated sentence of chunk does NOT falsely reject valid positive quote
    assert cv.validate_claim_citation(
        "Paid Social (LinkedIn Ads): Capped at a maximum allocation of $15,000.",
        Citation(document_id="DOC-MKT-002", chunk_id="DOC-MKT-002-C005", quote=pos_quote),
        [pos_rc],
    ).is_valid is True


# ---------------------------------------------------------------------------
# ADV-003: Zero influencer budget consistency
# ---------------------------------------------------------------------------
def test_adv003_zero_influencer_budget_not_conflict(tmp_path):
    wf = _wf(tmp_path)
    for req_id, val in [("ADV003-ZERO-INT", 0), ("ADV003-ZERO-FLT", 0.00)]:
        rec = wf.evaluate_proposal(_inf_req(req_id, val))
        assert rec.status == WorkflowStatus.AWAITING_APPROVAL
        assert rec.conflict is None
        assert rec.recommendation.recommended_action == "REVIEW"

    # Non-influencer $0 also routes to REVIEW
    rec_non_inf = wf.evaluate_proposal(
        WorkflowRequest(
            request_id="ADV003-NONINF-ZERO",
            title="Zero Budget LinkedIn Test",
            proposal_text="Deploy LinkedIn Sponsored Content for enterprise SQLs with zero spend.",
            requested_budget=0.0,
        )
    )
    assert rec_non_inf.status == WorkflowStatus.AWAITING_APPROVAL
    assert rec_non_inf.recommendation.recommended_action == "REVIEW"


# ---------------------------------------------------------------------------
# ADV-004: Provenance example manifest consistency
# ---------------------------------------------------------------------------
def test_adv004_provenance_example_manifest_ratified_status():
    p = Path("docs/proposals/marketing_manifest_provenance_example.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["proposal_status"] == "CMO_DOMAIN_RATIFIED_MDU_REGISTRATION_PENDING"
    assert len(data["documents"]) == 4
    for doc in data["documents"]:
        assert doc["freshness"]["sla_status"] == "RATIFIED"


# ---------------------------------------------------------------------------
# ADV-005: Request ID path-traversal and safety validation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "bad_id",
    [
        "../../evil_traversal",
        "../records",
        "/etc/passwd",
        r"C:\evil\path",
        "req/sub",
        r"req\sub",
        "req\x00null",
        "",
        "   ",
        "A" * 129,
    ],
)
def test_adv005_rejects_unsafe_request_ids(tmp_path, bad_id):
    wf = _wf(tmp_path)
    rec = wf.evaluate_proposal(
        WorkflowRequest(
            request_id=bad_id,
            title="Traversal Test",
            proposal_text="Deploy LinkedIn Sponsored Content campaign for enterprise SQLs.",
            requested_budget=10000.0,
        )
    )
    assert rec.status == WorkflowStatus.INVALID_REQUEST


@pytest.mark.parametrize(
    "good_id",
    [
        "550e8400-e29b-41d4-a716-446655440000",
        "REQ-MKT-2026-LI-01",
    ],
)
def test_adv005_allows_valid_request_ids(tmp_path, good_id):
    wf = _wf(tmp_path)
    rec = wf.evaluate_proposal(
        WorkflowRequest(
            request_id=good_id,
            title="Valid ID LinkedIn Test",
            proposal_text="Deploy LinkedIn Sponsored Content campaign for enterprise SQLs.",
            requested_budget=10000.0,
        )
    )
    assert rec.status == WorkflowStatus.AWAITING_APPROVAL
