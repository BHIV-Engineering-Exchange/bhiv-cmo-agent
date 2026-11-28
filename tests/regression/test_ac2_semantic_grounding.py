"""Regression tests for AC-2 claim-level semantic grounding and citation validation."""
from pathlib import Path
import pytest

from evidence_rag.evidence import CitationValidator
from evidence_rag.schemas import Chunk, RetrievedChunk, Citation
from evidence_rag.workflow import DecisionWorkflow
from evidence_rag.workflow_schemas import WorkflowRequest, WorkflowStatus
from evidence_rag.record_store import RecordStore


def _sample_retrieved() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk=Chunk(
                chunk_id="DOC-MKT-001-C003",
                document_id="DOC-MKT-001",
                chunk_index=2,
                text="The primary objective for Q4 is driving a 25% increase in sales-qualified enterprise leads (SQLs)."
            ),
            score=0.6,
            rank=1,
            raw_similarity=0.6
        ),
        RetrievedChunk(
            chunk=Chunk(
                chunk_id="DOC-MKT-002-C005",
                document_id="DOC-MKT-002",
                chunk_index=4,
                text="Active planned media spend cannot exceed $42,500.\n- **Paid Social (LinkedIn Ads):** Capped at a maximum allocation of $15,000."
            ),
            score=0.5,
            rank=2,
            raw_similarity=0.5
        ),
        RetrievedChunk(
            chunk=Chunk(
                chunk_id="DOC-MKT-003-C003",
                document_id="DOC-MKT-003",
                chunk_index=2,
                text="- **Click-Through Rate (CTR):** Average baseline across paid search and social is 2.4%."
            ),
            score=0.45,
            rank=3,
            raw_similarity=0.45
        ),
    ]


def test_claim_citation_rejects_missing_doc_and_chunk():
    validator = CitationValidator()
    retrieved = _sample_retrieved()

    res_doc = validator.validate_claim_citation(
        "The primary objective for Q4 is driving a 25% increase in sales-qualified enterprise leads (SQLs).",
        Citation(document_id="DOC-MKT-999", chunk_id="DOC-MKT-001-C003", quote="25% increase"),
        retrieved,
    )
    assert res_doc.is_valid is False

    res_chunk = validator.validate_claim_citation(
        "The primary objective for Q4 is driving a 25% increase in sales-qualified enterprise leads (SQLs).",
        Citation(document_id="DOC-MKT-001", chunk_id="DOC-MKT-001-C999", quote="25% increase"),
        retrieved,
    )
    assert res_chunk.is_valid is False


def test_claim_citation_rejects_mismatched_doc_and_chunk_ownership():
    validator = CitationValidator()
    retrieved = _sample_retrieved()
    res = validator.validate_claim_citation(
        "Paid Social (LinkedIn Ads): Capped at a maximum allocation of $15,000.",
        Citation(
            document_id="DOC-MKT-001",
            chunk_id="DOC-MKT-002-C005",
            quote="- **Paid Social (LinkedIn Ads):** Capped at a maximum allocation of $15,000."
        ),
        retrieved,
    )
    assert res.is_valid is False
    assert "belongs to DOC-MKT-002" in res.validation_reason


def test_claim_citation_rejects_truncated_statement_and_null_or_mismatched_quote():
    validator = CitationValidator()
    retrieved = _sample_retrieved()

    res_trunc = validator.validate_claim_citation(
        "ed data grounding, and high-reliability operational tooling.",
        Citation(document_id="DOC-MKT-001", chunk_id="DOC-MKT-001-C003", quote="25% increase"),
        retrieved,
    )
    assert res_trunc.is_valid is False

    res_null_quote = validator.validate_claim_citation(
        "The primary objective for Q4 is driving a 25% increase in sales-qualified enterprise leads (SQLs).",
        Citation(document_id="DOC-MKT-001", chunk_id="DOC-MKT-001-C003", quote=None),
        retrieved,
        require_quote=True,
    )
    assert res_null_quote.is_valid is False

    res_bad_quote = validator.validate_claim_citation(
        "The primary objective for Q4 is driving a 25% increase in sales-qualified enterprise leads (SQLs).",
        Citation(document_id="DOC-MKT-001", chunk_id="DOC-MKT-001-C003", quote="Fabricated quote not in chunk"),
        retrieved,
    )
    assert res_bad_quote.is_valid is False


def test_claim_citation_rejects_unsupported_claim_and_ctr_misattribution():
    validator = CitationValidator()
    retrieved = _sample_retrieved()

    res_unsupported = validator.validate_claim_citation(
        "LinkedIn Ads is capped at $99,000 for Q4 enterprise campaigns.",
        Citation(
            document_id="DOC-MKT-002",
            chunk_id="DOC-MKT-002-C005",
            quote="- **Paid Social (LinkedIn Ads):** Capped at a maximum allocation of $15,000."
        ),
        retrieved,
    )
    assert res_unsupported.is_valid is False

    res_ctr = validator.validate_claim_citation(
        "Average LinkedIn-only Click-Through Rate (CTR) baseline is 2.4%.",
        Citation(
            document_id="DOC-MKT-003",
            chunk_id="DOC-MKT-003-C003",
            quote="- **Click-Through Rate (CTR):** Average baseline across paid search and social is 2.4%."
        ),
        retrieved,
    )
    assert res_ctr.is_valid is False
    assert "Misattribution" in res_ctr.validation_reason


def test_ac2_linkedin_commercial_scenario_grounds_all_required_claims(tmp_path):
    """Verify REQ-MKT-2026-LI-01 extracts complete, verbatim-quoted facts across DOC-MKT-001/002/003."""
    wf = DecisionWorkflow(
        config_path="configs/marketing_workflow.yaml",
        record_store=RecordStore(tmp_path / "records")
    )
    req = WorkflowRequest(
        request_id="REQ-MKT-2026-LI-01-TEST",
        title="Q4 Enterprise LinkedIn Lead Gen Campaign",
        proposal_text=(
            "Deploy targeted sponsored content on LinkedIn targeting technical decision makers "
            "(Engineering Managers, VP of Engineering, CTOs), aiming to drive a 25% increase in "
            "sales-qualified enterprise leads (SQLs) via Paid Social (LinkedIn Ads) with requested "
            "budget of $30,000.00 USD."
        ),
        department="Marketing",
        requested_budget=30000.0,
        submitted_by="analyst@bhiv.internal",
        metadata={"channel": "Paid Social (LinkedIn Ads)", "objective": "25% increase in SQLs"}
    )
    rec = wf.evaluate_proposal(req)

    assert rec.status == WorkflowStatus.AWAITING_APPROVAL
    facts = rec.recommendation.verified_facts
    assert len(facts) >= 5
    all_statements = " ".join(f.statement for f in facts)

    # All required claims must be present and validated with non-null quotes
    assert "25% increase" in all_statements
    assert "LinkedIn Sponsored Content" in all_statements
    assert "$15,000" in all_statements
    assert "2.4%" in all_statements or "$32.00" in all_statements
    for f in facts:
        assert f.citation.is_valid is True
        assert f.citation.quote is not None and len(f.citation.quote) > 10
        assert not f.statement[0].islower()
