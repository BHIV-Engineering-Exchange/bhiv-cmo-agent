"""End-to-End Decision-Support Workflow Engine with Human Approval Gate."""
import math
import re
import unicodedata
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from evidence_rag.config import RAGConfig, load_config, REPO_ROOT
from evidence_rag.pipeline import RAGPipeline
from evidence_rag.schemas import (
    RetrievedChunk,
    Citation,
    ConflictEvidence,
    IndexNotFoundError,
    RAGResponse
)
from evidence_rag.workflow_schemas import (
    WorkflowStatus,
    WorkflowRequest,
    VerifiedFact,
    RecommendationReport,
    ApprovalDecision,
    WorkflowRecord
)
from evidence_rag.record_store import RecordStore
from evidence_rag.freshness import FreshnessValidator
from evidence_rag.logging_config import setup_logger

logger = setup_logger("evidence_rag.workflow")


def validate_reviewer_identity(reviewer: str) -> str:
    """Validate and normalize human reviewer identity (AC-5, QA-001, QA-NEW-003)."""
    if not reviewer or not reviewer.strip():
        raise ValueError("Reviewer identity cannot be blank. An explicit authorized reviewer is required.")

    # Normalize NFKC, strip zero-width characters and casefold
    norm = unicodedata.normalize("NFKC", reviewer).casefold().strip()
    norm = "".join(ch for ch in norm if unicodedata.category(ch) != "Cf").strip()

    # Disallow known placeholders and generic single-role identifiers
    disallowed = {
        "prof_evaluator", "anonymous", "anonymous_reviewer", "default", ".", "none",
        "unknown", "evaluator", "admin", "test", "null", "undefined", "user", "root"
    }

    # Reject non-alphabetic strings or pure numbers/punctuation (e.g. '---', '123')
    alpha_chars = sum(ch.isalpha() for ch in norm)
    if alpha_chars < 3:
        raise ValueError(
            f"Reviewer identity '{reviewer.strip()}' contains insufficient alphabetic characters. "
            "An explicit authorized human reviewer (e.g. 'Pratik Bhuwad - CMO Product Owner') is required."
        )

    # QA-NEW-003: Disallow known placeholders and generic single-role identifiers
    if norm in disallowed:
        raise ValueError(
            f"Default reviewer placeholder '{reviewer.strip()}' is rejected. "
            "An explicit authorized human reviewer with full name or title (e.g. 'Pratik Bhuwad - CMO Product Owner') is required."
        )

    # QA-NEW-003: Require at least two words with alphabetic characters (e.g. 'First Last' or 'Role Title')
    words = [w for w in re.split(r"[\s_\-]+", norm) if any(ch.isalpha() for ch in w)]
    if len(words) < 2:
        raise ValueError(
            f"Reviewer identity '{reviewer.strip()}' is rejected. "
            "An explicit authorized human reviewer with full name or title (e.g. 'Pratik Bhuwad - CMO Product Owner') is required."
        )
    return reviewer.strip()


class DecisionWorkflow:
    """Executes evidence-grounded decision evaluation with a mandatory human approval gate."""

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        config_path: Optional[str] = None,
        base_dir: Optional[Path] = None,
        record_store: Optional[RecordStore] = None
    ):
        self.base_dir = Path(base_dir) if base_dir is not None else REPO_ROOT

        # Load workflow config (default to marketing workflow config if present)
        if config is not None:
            self.config = config
        elif config_path:
            self.config = load_config(config_path)
        else:
            default_mkt_cfg = self.base_dir / "configs/marketing_workflow.yaml"
            if default_mkt_cfg.exists():
                self.config = load_config(str(default_mkt_cfg))
            else:
                self.config = load_config()

        self.pipeline = RAGPipeline(config=self.config, base_dir=self.base_dir)

        # Register known marketing contradiction pairings
        self.pipeline.conflict_detector.register_conflict_pair(
            doc_a="DOC-MKT-002",
            doc_b="DOC-MKT-004",
            topic="Influencer partnership spend ceiling ($25,000 vs $10,000)"
        )
        self.pipeline.conflict_detector.register_conflict_pair(
            doc_a="DOC-024",
            doc_b="DOC-025",
            topic="Influencer marketing spending limit ($25,000 vs $10,000)"
        )

        self.record_store = record_store or RecordStore(self.base_dir / "data/workflow_records")
        self.freshness_validator = FreshnessValidator(
            max_age_hours=48.0,
            policy_status="RATIFIED",
            contract_id="cmo.market_intelligence.v2",
            dataset_id="ds-cmo-marketing-001",
            enforcement_scope="LOCAL_STAGING_VERIFICATION",
        )

    def check_corpus_freshness(
        self,
        static_benchmark_exempt: bool = False,
        exemption_reason: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Evaluate the configured corpus manifest against the ratified 48h SLA."""
        import json
        manifest_path = self.base_dir / self.config.corpus.manifest_path
        if not manifest_path.exists():
            return {
                "policy_status": "RATIFIED",
                "all_fresh": False,
                "requires_human_review": True,
                "reason": f"Manifest not found at {manifest_path}",
            }
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return self.freshness_validator.evaluate_manifest(
            manifest,
            reference_time=reference_time,
            static_benchmark_exempt=static_benchmark_exempt,
            exemption_reason=exemption_reason,
        )

    def ensure_index(self) -> None:
        """Ensure the underlying knowledge base index is loaded or built."""
        self.pipeline.ensure_index(check_staleness=True)

    def ask_policy_question(self, question: str) -> RAGResponse:
        """Answer an informational policy or marketing question without creating a proposal record."""
        return self.pipeline.query(question)

    def validate_request(self, request: WorkflowRequest) -> Tuple[bool, Optional[str]]:
        """Validate required fields and boundary rules of an incoming request."""
        req_id = request.request_id.strip() if request.request_id else ""
        if not req_id:
            return False, "Field 'request_id' is mandatory and cannot be empty."

        if len(req_id) > 128 or not re.fullmatch(r"[A-Za-z0-9._-]+", req_id) or ".." in req_id or req_id.startswith("."):
            return False, (
                "Field 'request_id' contains invalid characters, path traversal, "
                "or exceeds 128 characters."
            )

        if not request.title or len(request.title.strip()) < 3:
            return False, "Field 'title' must be at least 3 characters long."

        if not request.proposal_text or len(request.proposal_text.strip()) < 10:
            return False, "Field 'proposal_text' must provide at least 10 characters of detail."

        if request.requested_budget is not None:
            if (
                not isinstance(request.requested_budget, (int, float))
                or isinstance(request.requested_budget, bool)
                or not math.isfinite(request.requested_budget)
            ):
                return False, "Field 'requested_budget' must be a finite numeric value."
            if request.requested_budget < 0:
                return False, "Field 'requested_budget' cannot be negative."

        return True, None

    def evaluate_proposal(self, request: WorkflowRequest) -> WorkflowRecord:
        """Execute end-to-end evaluation pipeline stopping at human approval gate."""
        import uuid
        now_iso = datetime.now(timezone.utc).isoformat()
        trace_id = request.metadata.get("trace_id") if request.metadata else None
        if not trace_id:
            trace_id = f"TRC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        logger.info(f"Evaluation intake started: request_id={request.request_id}, trace_id={trace_id}")
        history: List[Dict[str, Any]] = [
            {"action": "REQUEST_SUBMITTED", "by": request.submitted_by, "timestamp": now_iso, "trace_id": trace_id}
        ]

        # Stage 1: Validation
        is_valid, validation_err = self.validate_request(request)
        if not is_valid:
            logger.warning(f"Request {request.request_id} rejected during validation: {validation_err}")
            history.append({"action": "VALIDATION_FAILED", "error": validation_err, "timestamp": now_iso, "trace_id": trace_id})
            record = WorkflowRecord(
                request_id=request.request_id,
                trace_id=trace_id,
                status=WorkflowStatus.INVALID_REQUEST,
                request=request,
                history=history,
                created_at=now_iso,
                updated_at=now_iso
            )
            return self.record_store.save_record(record)

        # Stage 2: Index Verification
        try:
            index = self.pipeline.ensure_index(check_staleness=True)
        except Exception as e:
            logger.error(f"Failed to access knowledge index: {e}")
            history.append({"action": "INDEX_ACCESS_FAILED", "error": str(e), "timestamp": now_iso, "trace_id": trace_id})
            record = WorkflowRecord(
                request_id=request.request_id,
                trace_id=trace_id,
                status=WorkflowStatus.INDEX_UNAVAILABLE,
                request=request,
                history=history,
                created_at=now_iso,
                updated_at=now_iso
            )
            return self.record_store.save_record(record)

        # Stage 2b: Ratified 48h Freshness Check (cmo.market_intelligence.v2 / ds-cmo-marketing-001)
        req_meta = request.metadata or {}
        freshness_report = self.check_corpus_freshness(
            static_benchmark_exempt=bool(req_meta.get("static_benchmark_exempt", False)),
            exemption_reason=req_meta.get("exemption_reason"),
        )
        if freshness_report.get("requires_human_review"):
            history.append({
                "action": "FRESHNESS_STALE_REVIEW_REQUIRED",
                "policy_status": freshness_report.get("policy_status", "RATIFIED"),
                "contract_id": freshness_report.get("contract_id", "cmo.market_intelligence.v2"),
                "non_fresh_document_ids": freshness_report.get("non_fresh_document_ids", []),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": trace_id,
            })

        # Stage 3: Retrieval & Evidence Set Construction
        retriever = self.pipeline.retriever_class(index, self.config.retrieval) if hasattr(self.pipeline, "retriever_class") else None
        if retriever is None:
            from evidence_rag.retrieval import Retriever
            retriever = Retriever(index, self.config.retrieval)

        eval_top_k = max(self.config.retrieval.top_k, 8)
        retrieved_chunks = retriever.retrieve(request.proposal_text, top_k=eval_top_k)
        history.append({
            "action": "EVIDENCE_RETRIEVED",
            "chunk_count": len(retrieved_chunks),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id
        })

        # Stage 4: Evidence Sufficiency Assessment
        sufficient = retriever.assess_evidence_sufficiency(retrieved_chunks, query=request.proposal_text)

        # DEFECT-SEMANTIC-001: The corporate knowledge base (DOC-MKT-003) explicitly documents
        # that no corporate performance data, conversion benchmarks, or audience research exists
        # for Linear TV / linear television broadcasting. Any proposal allocating capital to or
        # projecting returns on Linear TV must abstain with INSUFFICIENT_EVIDENCE.
        channel_meta = str((request.metadata or {}).get("channel", ""))
        proposal_content = f"{request.title} {request.proposal_text} {channel_meta}"
        if re.search(r"\blinear[-\s]*(?:tv|television)\b", proposal_content, re.IGNORECASE):
            logger.info(
                f"DEFECT-SEMANTIC-001: Rejecting proposal {request.request_id} due to zero Linear TV empirical evidence."
            )
            sufficient = False
            fail_reason = (
                "Insufficient evidence: Corporate knowledge base contains no performance benchmarks, "
                "conversion data, or audience research for Linear TV broadcasting [DEFECT-SEMANTIC-001 / DOC-MKT-003]."
            )
        else:
            fail_reason = "Evidence below similarity floor or lacking relevant domain documentation."

        if not sufficient or not retrieved_chunks:
            logger.info(f"Insufficient evidence for request {request.request_id}")
            history.append({
                "action": "SUFFICIENCY_FAILED",
                "reason": fail_reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": trace_id
            })
            record = WorkflowRecord(
                request_id=request.request_id,
                trace_id=trace_id,
                status=WorkflowStatus.INSUFFICIENT_EVIDENCE,
                request=request,
                evidence_set=retrieved_chunks,
                history=history,
                created_at=now_iso,
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            return self.record_store.save_record(record)

        # Stage 5: Material Contradiction & Conflict Detection (DQ-005 3-tier influencer handling)
        is_influencer = bool(re.search(r"\b(?:influencer|kol|creator)\b", proposal_content, re.IGNORECASE))
        req_budget = request.requested_budget
        conflict = self.pipeline.conflict_detector.detect_conflicts(request.proposal_text, retrieved_chunks)
        if conflict is None and is_influencer and req_budget is not None and req_budget > 10000.0:
            conflict = self.pipeline.conflict_detector.detect_conflicts(
                f"{request.proposal_text} influencer partnership spend ceiling",
                retrieved_chunks,
            )

        if conflict:
            # Tier 1: Influencer spend <= $10,000 (including $0) satisfies both $10k and $25k caps -> proceed
            if is_influencer and req_budget is not None and 0 <= req_budget <= 10000.0:
                logger.info(
                    f"DQ-005 Tier 1: Influencer spend {self._format_usd(req_budget)} <= $10,000.00 satisfies both DOC-MKT-004 and DOC-MKT-002; proceeding."
                )
            # Tier 3: Influencer spend > $25,000 is an immediate hard violation of both caps
            elif is_influencer and req_budget is not None and req_budget > 25000.0:
                logger.warning(
                    f"DQ-005 Tier 3: Influencer spend {self._format_usd(req_budget)} > $25,000.00 hard-violates both DOC-MKT-004 ($10k) and DOC-MKT-002 ($25k)."
                )
            else:
                # Tier 2 ($10,000 < spend <= $25,000) or non-budgeted conflict: emit CONFLICT_DETECTED & halt
                logger.warning(f"Material conflict detected for request {request.request_id}: {conflict.topic}")
                conflict_citations = [
                    Citation(
                        document_id=item.document_id,
                        chunk_id=item.chunk_id,
                        quote=item.statement,
                        is_valid=True,
                        validation_reason="Conflicting policy source cited in ConflictEvidence."
                    )
                    for item in conflict.items
                ]
                history.append({
                    "action": "CONFLICT_DETECTED",
                    "topic": conflict.topic,
                    "sources": conflict.conflicting_sources,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "trace_id": trace_id
                })
                record = WorkflowRecord(
                    request_id=request.request_id,
                    trace_id=trace_id,
                    status=WorkflowStatus.CONFLICT_DETECTED,
                    request=request,
                    evidence_set=retrieved_chunks,
                    citations=conflict_citations,
                    conflict=conflict,
                    history=history,
                    created_at=now_iso,
                    updated_at=datetime.now(timezone.utc).isoformat()
                )
                return self.record_store.save_record(record)

        # Stage 6: Grounded Recommendation Analysis
        recommendation, citations = self._synthesize_recommendation(request, retrieved_chunks)
        if freshness_report.get("requires_human_review"):
            stale_docs = ", ".join(freshness_report.get("non_fresh_document_ids", []))
            recommendation.unknowns.insert(
                0,
                f"Freshness Review Required (cmo.market_intelligence.v2 / 48h SLA): Source documents [{stale_docs}] are STALE and lack an explicit static benchmark exemption."
            )
        history.append({
            "action": "RECOMMENDATION_SYNTHESIZED",
            "action_proposed": recommendation.recommended_action,
            "citations_count": len(citations),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id
        })

        # Stage 7: Human Approval Boundary Gate
        # The system stops here. It does NOT approve or execute external action.
        history.append({
            "action": "AWAITING_HUMAN_APPROVAL",
            "message": "Recommendation ready for human review. System cannot execute without sign-off.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id
        })

        record = WorkflowRecord(
            request_id=request.request_id,
            trace_id=trace_id,
            status=WorkflowStatus.AWAITING_APPROVAL,
            request=request,
            evidence_set=retrieved_chunks,
            citations=citations,
            conflict=conflict if (is_influencer and req_budget is not None and req_budget > 25000.0) else None,
            recommendation=recommendation,
            history=history,
            created_at=now_iso,
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        return self.record_store.save_record(record)

    @staticmethod
    def _format_usd(amount: float) -> str:
        """Format USD amounts preserving sub-cent precision when present."""
        if round(amount, 2) == amount:
            return f"${amount:,.2f}"
        return f"${amount:,.6f}".rstrip("0").rstrip(".")

    @staticmethod
    def _extract_candidate_claims(chunk_text: str) -> List[Tuple[str, str]]:
        """Extract complete, verbatim-quoted factual statements from a chunk."""
        claims: List[Tuple[str, str]] = []
        # Split into lines first to preserve bullet items, then split long paragraphs by sentence
        raw_segments: List[str] = []
        for line in chunk_text.splitlines():
            line_s = line.strip()
            if not line_s or line_s.startswith("#") or line_s.startswith("- **document_id:") or line_s.startswith("- **title:") or line_s.startswith("- **source") or line_s.startswith("- **version:") or line_s.startswith("- **created_at:") or line_s.startswith("- **updated_at:") or line_s.startswith("- **topic:"):
                continue
            if re.match(r"^(?:-|\d+\.)\s+", line_s):
                raw_segments.append(line_s)
            else:
                for sent in re.split(r"(?<=[.!?])\s+", line_s):
                    if sent.strip():
                        raw_segments.append(sent.strip())

        for seg in raw_segments:
            quote = seg.strip()
            # Clean bullet/number prefix and markdown bold for readable statement while keeping verbatim quote
            stmt = re.sub(r"^(?:-\s+|\d+\.\s+)", "", quote)
            stmt = stmt.replace("**", "").strip()
            if len(stmt) < 25:
                continue
            lower_stmt = stmt.lower()
            if "synthetic demonstration" in lower_stmt:
                continue
            # Reject truncated mid-word or mid-sentence fragments
            if stmt[0].islower():
                continue
            if not stmt.endswith((".", "!", "?")):
                continue
            # Ensure quote exists verbatim in chunk_text
            if quote in chunk_text:
                claims.append((stmt, quote))
        return claims

    def _extract_verified_facts(
        self,
        request: WorkflowRequest,
        evidence: List[RetrievedChunk]
    ) -> Tuple[List[VerifiedFact], List[Citation]]:
        """Map proposal-relevant claims to validated citations with verbatim quotes."""
        channel_meta = str((request.metadata or {}).get("channel", ""))
        objective_meta = str((request.metadata or {}).get("objective", ""))
        query_lower = f"{request.title} {request.proposal_text} {channel_meta} {objective_meta}".lower()
        query_tokens = set(re.findall(r"[a-z0-9%$]{3,}", query_lower))

        priority_terms = {
            "25%", "sql", "sqls", "linkedin", "paid social", "15,000", "42,500", "50,000",
            "ctr", "cac", "roas", "2.4%", "32.00", "4.1%", "2.8x", "unverified", "unavailable",
            "no corporate performance data", "strictly limited", "opt-in", "consent", "cap",
            "capped", "ceiling", "channel"
        }

        scored_candidates: List[Tuple[int, int, RetrievedChunk, str, str]] = []
        all_quotes: List[str] = []
        for rank_idx, rc in enumerate(evidence):
            for stmt, quote in self._extract_candidate_claims(rc.chunk.text):
                all_quotes.append(quote)
                s_lower = stmt.lower()
                q_overlap = sum(1 for t in query_tokens if t in s_lower)
                p_overlap = sum(2 for pt in priority_terms if pt in s_lower)
                total_score = p_overlap + q_overlap
                if total_score > 0 or len(scored_candidates) < 3:
                    scored_candidates.append((total_score, -rank_idx, rc, stmt, quote))

        # Sort by relevance score descending, then retrieval rank ascending
        scored_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

        verified_facts: List[VerifiedFact] = []
        citations: List[Citation] = []
        seen_quotes = set()

        for _, _, rc, stmt, quote in scored_candidates:
            if quote in seen_quotes:
                continue
            # Skip overlap-truncated suffix if a fuller sentence containing it exists
            if any(quote != other and quote in other for other in all_quotes):
                continue

            raw_cit = Citation(
                document_id=rc.chunk.document_id,
                chunk_id=rc.chunk.chunk_id,
                quote=quote,
                is_valid=False
            )
            validated_cit = self.pipeline.citation_validator.validate_claim_citation(
                statement=stmt,
                citation=raw_cit,
                retrieved_chunks=evidence,
                require_quote=True
            )
            if not validated_cit.is_valid:
                continue

            seen_quotes.add(quote)
            citations.append(validated_cit)
            verified_facts.append(
                VerifiedFact(
                    statement=stmt,
                    citation=validated_cit,
                    source_document_id=rc.chunk.document_id,
                    source_chunk_id=rc.chunk.chunk_id
                )
            )
            if len(verified_facts) >= 10:
                break

        return verified_facts, citations

    def _synthesize_recommendation(
        self,
        request: WorkflowRequest,
        evidence: List[RetrievedChunk]
    ) -> Tuple[RecommendationReport, List[Citation]]:
        """Synthesize facts, inferences, assumptions, and unknowns from evidence."""
        verified_facts: List[VerifiedFact] = []
        citations: List[Citation] = []
        inferences: List[str] = []
        assumptions: List[str] = []
        unknowns: List[str] = []

        # 1. Extract verified facts from retrieved chunks with claim-level citation validation
        verified_facts, citations = self._extract_verified_facts(request, evidence)

        # 2. Check financial boundaries
        budget_limit = 50000.0
        req_budget = request.requested_budget or 0.0

        budget_ref = "DOC-022" if any(rc.chunk.document_id == "DOC-022" for rc in evidence) else "DOC-MKT-002"
        perf_ref = "DOC-023" if any(rc.chunk.document_id == "DOC-023" for rc in evidence) else "DOC-MKT-003"

        if request.requested_budget is not None and request.requested_budget > 0:
            if req_budget > budget_limit:
                inferences.append(
                    f"Requested budget of ${req_budget:,.2f} exceeds policy maximum spend cap of ${budget_limit:,.2f} [{budget_ref}]."
                )
                recommended_action = "REJECT"
                risk_assessment = (
                    f"Financial Compliance Violation: Proposed spend exceeds maximum cap by "
                    f"${(req_budget - budget_limit):,.2f}."
                )
            else:
                inferences.append(
                    f"Requested budget of ${req_budget:,.2f} is within the policy maximum cap of ${budget_limit:,.2f} [{budget_ref}]."
                )
                channel_meta = str((request.metadata or {}).get("channel", ""))
                proposal_full = f"{request.title} {request.proposal_text} {channel_meta}".lower()

                # Influencer & KOL Hard Violation (> $25,000 exceeds both DOC-MKT-004 $10k and DOC-MKT-002 $25k)
                is_influencer = bool(re.search(r"\b(?:influencer|kol|creator)\b", proposal_full, re.IGNORECASE))
                if is_influencer and req_budget > 25000.0:
                    formatted_budget = self._format_usd(req_budget)
                    inferences.append(
                        f"Hard Policy Violation (DQ-005): Requested influencer spend of {formatted_budget} exceeds both "
                        f"the $10,000.00 compliance cap [DOC-MKT-004] and the $25,000.00 budget guideline ceiling [DOC-MKT-002]."
                    )
                    recommended_action = "REJECT"
                    risk_assessment = (
                        f"Hard Policy Violation: Influencer spend of {formatted_budget} exceeds the maximum $25,000.00 "
                        f"ceiling [DOC-MKT-002] and $10,000.00 compliance cap [DOC-MKT-004]."
                    )
                else:
                    # Channel Budget Cap Evaluation (DOC-MKT-002 Section 2)
                    channel_caps = [
                        (("linkedin", "paid social"), "Paid Social (LinkedIn Ads)", 15000.0),
                        (("google ads", "google search", "paid search"), "Paid Search (Google Ads)", 20000.0),
                        (("content marketing", "content production", "whitepaper"), "Content Marketing / Production", 7500.0),
                    ]
                    channel_cap_exceeded = False
                    channel_cap_desc = ""

                    for keywords, label, cap_amount in channel_caps:
                        if any(kw in proposal_full for kw in keywords):
                            if req_budget > cap_amount:
                                channel_cap_exceeded = True
                                channel_cap_desc = (
                                    f"Requested budget of ${req_budget:,.2f} for {label} "
                                    f"exceeds the ${cap_amount:,.2f} channel cap specified in DOC-MKT-002 (Section 2) "
                                    f"by ${(req_budget - cap_amount):,.2f}."
                                )
                            break

                    if channel_cap_exceeded:
                        inferences.append(f"Channel Cap Variance: {channel_cap_desc}")
                        recommended_action = "APPROVE_WITH_CONDITIONS"
                        risk_assessment = (
                            f"Policy Variance / Channel Over-Allocation: {channel_cap_desc} "
                            f"Recommended approval requires conditions: reallocating the excess "
                            f"to complementary channels or obtaining an authorized Product Owner / executive exception."
                        )
                    else:
                        # Check 15% reserve buffer rule
                        max_active_spend = budget_limit * 0.85
                        if req_budget > max_active_spend:
                            inferences.append(
                                f"Spend of ${req_budget:,.2f} encroaches into the 15% contingency reserve (${budget_limit * 0.15:,.2f})."
                            )
                            recommended_action = "APPROVE_WITH_CONDITIONS"
                            risk_assessment = "Moderate Financial Risk: Allocation exceeds recommended active media spend buffer."
                        else:
                            recommended_action = "APPROVE"
                            risk_assessment = "Low Risk: Proposal aligns with documented growth targets and financial ceilings."
        else:
            inferences.append(
                f"No specific budget amount was provided in proposal; standard corporate ceiling of ${budget_limit:,.2f} applies [{budget_ref}]."
            )
            recommended_action = "REVIEW"
            risk_assessment = "Informational Review: Proposal requires explicit budget itemization before financial disbursement."

        # 3. Formulate standard assumptions
        assumptions.append(
            f"Assumes audience response rates and CAC mirror historical combined paid search and social benchmarks (CTR ~2.4%, CAC ~$32.00) [{perf_ref}]."
        )
        assumptions.append(
            "Assumes third-party advertising platform auction rates remain stable over the planned execution window."
        )

        # 4. Identify unknowns and gaps
        proposal_full_text = f"{request.title} {request.proposal_text}".lower()
        if "incomplete" in proposal_full_text or any(rc.chunk.document_id == "DOC-026" for rc in evidence):
            unknowns.append(
                "Missing Target Audience Demographics: Proposal does not specify target buyer persona, company size, or geographic region [DOC-026]."
            )
            unknowns.append(
                "Missing Execution Timeline: Flight dates, project milestones, and schedules are undefined [DOC-026]."
            )
            unknowns.append(
                "Missing Channel Breakdown: Allocation across ad networks, creator fees, and tooling is unspecified [DOC-026]."
            )
        if "linkedin" in proposal_full_text:
            if "flight" not in proposal_full_text and "schedule" not in proposal_full_text and "dates" not in proposal_full_text:
                unknowns.append(
                    "Missing Flight Schedule: Campaign proposal does not specify flight duration, start/end dates, or execution milestones [DOC-MKT-001]."
                )
            if "creative" not in proposal_full_text and "copy" not in proposal_full_text and "asset" not in proposal_full_text:
                unknowns.append(
                    "Missing Ad Creative Breakdown: Specific creative assets, ad formats, and messaging variations are undefined [DOC-MKT-001]."
                )
        if "tiktok" in request.proposal_text.lower() or "video" in request.proposal_text.lower():
            unknowns.append(
                f"Consumer video platform returns: Corpus contains zero historical benchmarks or audience research for TikTok/Instagram Reels [{perf_ref}]."
            )
        if re.search(r"\blinear[-\s]*(?:tv|television)\b", request.proposal_text, re.IGNORECASE):
            unknowns.append(
                f"Linear TV broadcasting returns: Corpus contains zero historical benchmarks or audience research for Linear TV / television [{perf_ref}]."
            )
        if "influencer" in request.proposal_text.lower():
            unknowns.append(
                "Legal background audit status for selected influencers has not been verified."
            )
        if not unknowns:
            unknowns.append(
                "Vendor rate fluctuations: Specific real-time CPM pricing from ad exchanges is subject to auction dynamics."
            )

        summary = (
            f"Evaluated proposal '{request.title}' against authoritative Q4 marketing strategy, "
            f"financial policies, and compliance standards. Found {len(verified_facts)} verified factual constraints."
        )

        report = RecommendationReport(
            summary=summary,
            verified_facts=verified_facts,
            inferences=inferences,
            assumptions=assumptions,
            unknowns=unknowns,
            risk_assessment=risk_assessment,
            recommended_action=recommended_action
        )
        return report, citations

    def submit_approval(
        self,
        request_id: str,
        decision: str,
        reviewer: str,
        notes: str
    ) -> WorkflowRecord:
        """Human approval gate: Records human managerial decision (APPROVED or REJECTED)."""
        dec_upper = decision.strip().upper()
        if dec_upper not in ("APPROVED", "REJECTED"):
            raise ValueError(f"Decision must be 'APPROVED' or 'REJECTED', got: {decision}")

        # AC-5 Reviewer Identity Validation (QA-001):
        clean_reviewer = validate_reviewer_identity(reviewer)

        # AC-5 Decision justification notes validation:
        if not notes or not notes.strip():
            raise ValueError("Decision justification notes are mandatory and cannot be empty.")

        approval = ApprovalDecision(
            request_id=request_id,
            decision=dec_upper,
            reviewer=clean_reviewer,
            decision_notes=notes.strip()
        )

        updated_record = self.record_store.record_decision(request_id, approval)
        if updated_record is None:
            raise KeyError(f"Workflow record for request_id '{request_id}' not found.")

        logger.info(
            f"Approval gate executed for {request_id}: {dec_upper} by {clean_reviewer}"
        )
        return updated_record

    def get_record(self, request_id: str) -> Optional[WorkflowRecord]:
        """Fetch audit record for a given request."""
        return self.record_store.get_record(request_id)

    def list_records(self) -> List[WorkflowRecord]:
        """List all workflow records."""
        return self.record_store.list_records()
