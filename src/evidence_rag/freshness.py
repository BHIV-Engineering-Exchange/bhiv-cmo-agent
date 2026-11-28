"""Configurable freshness and provenance timestamp validation (RATIFIED for cmo.market_intelligence.v2)."""
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FreshnessStatus(str, Enum):
    """Freshness classification for source documents and intelligence records."""
    FRESH = "FRESH"
    STALE = "STALE"
    EXEMPT_STATIC_BENCHMARK = "EXEMPT_STATIC_BENCHMARK"
    MISSING_TIMESTAMP = "MISSING_TIMESTAMP"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    FUTURE_DATED = "FUTURE_DATED"


class FreshnessResult(BaseModel):
    """Result of evaluating a single source record against the freshness policy."""
    document_id: str
    status: FreshnessStatus
    is_fresh: bool
    requires_human_review: bool = False
    age_hours: Optional[float] = None
    max_age_hours: float = 48.0
    policy_status: str = Field(
        default="RATIFIED",
        description="Formally ratified by PO for cmo.market_intelligence.v2 (local/staging verification only)"
    )
    contract_id: str = "cmo.market_intelligence.v2"
    dataset_id: str = "ds-cmo-marketing-001"
    enforcement_scope: str = "LOCAL_STAGING_VERIFICATION"
    static_benchmark_exempt: bool = False
    exemption_reason: Optional[str] = None
    timestamp_checked: Optional[str] = None
    reason: str


class FreshnessValidator:
    """Validates source timestamps against the ratified 48-hour marketing freshness SLA.

    Contract: cmo.market_intelligence.v2 | Dataset: ds-cmo-marketing-001
    Scope: Local development and staging verification only (no production/live integrations).
    Static benchmark exemptions must be explicit and documented, never inferred.
    """

    def __init__(
        self,
        max_age_hours: float = 48.0,
        policy_status: str = "RATIFIED",
        contract_id: str = "cmo.market_intelligence.v2",
        dataset_id: str = "ds-cmo-marketing-001",
        enforcement_scope: str = "LOCAL_STAGING_VERIFICATION",
    ):
        if max_age_hours <= 0:
            raise ValueError("max_age_hours must be positive.")
        self.max_age_hours = max_age_hours
        self.policy_status = policy_status
        self.contract_id = contract_id
        self.dataset_id = dataset_id
        self.enforcement_scope = enforcement_scope

    @staticmethod
    def parse_utc_timestamp(ts_value: Optional[str]) -> datetime:
        """Parse an ISO 8601 timestamp string and normalize to UTC."""
        if not ts_value or not isinstance(ts_value, str) or not ts_value.strip():
            raise ValueError("Timestamp is missing or empty.")
        raw = ts_value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            # Naive timestamps are rejected to prevent silent timezone ambiguity
            raise ValueError(f"Timestamp '{ts_value}' lacks explicit timezone offset or 'Z'.")
        return dt.astimezone(timezone.utc)

    def evaluate_timestamp(
        self,
        document_id: str,
        timestamp_str: Optional[str],
        reference_time: Optional[datetime] = None,
        static_benchmark_exempt: bool = False,
        exemption_reason: Optional[str] = None,
    ) -> FreshnessResult:
        """Evaluate whether a document timestamp satisfies the freshness SLA."""
        ref = (reference_time or datetime.now(timezone.utc)).astimezone(timezone.utc)

        def _make_result(
            status: FreshnessStatus,
            is_fresh: bool,
            reason: str,
            age_hours: Optional[float] = None,
            ts_checked: Optional[str] = timestamp_str,
            exempt: bool = False,
            ex_reason: Optional[str] = None,
        ) -> FreshnessResult:
            return FreshnessResult(
                document_id=document_id,
                status=status,
                is_fresh=is_fresh,
                requires_human_review=not is_fresh,
                age_hours=age_hours,
                max_age_hours=self.max_age_hours,
                policy_status=self.policy_status,
                contract_id=self.contract_id,
                dataset_id=self.dataset_id,
                enforcement_scope=self.enforcement_scope,
                static_benchmark_exempt=exempt,
                exemption_reason=ex_reason,
                timestamp_checked=ts_checked,
                reason=reason,
            )

        if not timestamp_str or not isinstance(timestamp_str, str) or not timestamp_str.strip():
            return _make_result(
                FreshnessStatus.MISSING_TIMESTAMP,
                False,
                "Missing source timestamp; cannot treat unknown freshness as current.",
                ts_checked=None,
            )

        try:
            dt = self.parse_utc_timestamp(timestamp_str)
        except Exception as exc:
            return _make_result(
                FreshnessStatus.INVALID_TIMESTAMP,
                False,
                f"Invalid timestamp '{timestamp_str}': {exc}",
            )

        age_hours = (ref - dt).total_seconds() / 3600.0
        if age_hours < -0.05:  # Allow minor sub-minute clock skew (3 minutes)
            return _make_result(
                FreshnessStatus.FUTURE_DATED,
                False,
                f"Timestamp '{timestamp_str}' is future-dated relative to {ref.isoformat()}.",
                age_hours=round(age_hours, 2),
            )

        if age_hours > self.max_age_hours:
            # Explicit, documented static benchmark exemption only (never inferred)
            if static_benchmark_exempt and exemption_reason and exemption_reason.strip():
                return _make_result(
                    FreshnessStatus.EXEMPT_STATIC_BENCHMARK,
                    True,
                    f"Source age {age_hours:.2f}h exceeds 48h SLA but has explicit static benchmark exemption: {exemption_reason.strip()}",
                    age_hours=round(age_hours, 2),
                    exempt=True,
                    ex_reason=exemption_reason.strip(),
                )
            return _make_result(
                FreshnessStatus.STALE,
                False,
                (
                    f"Source age {age_hours:.2f}h exceeds {self.policy_status} "
                    f"{self.max_age_hours:.1f}h freshness SLA; human review or refresh required."
                ),
                age_hours=round(age_hours, 2),
            )

        return _make_result(
            FreshnessStatus.FRESH,
            True,
            f"Source age {max(0.0, age_hours):.2f}h is within {self.max_age_hours:.1f}h SLA.",
            age_hours=round(max(0.0, age_hours), 2),
        )

    def evaluate_manifest(
        self,
        manifest: Dict[str, Any],
        reference_time: Optional[datetime] = None,
        timestamp_field: str = "updated_at",
        static_benchmark_exempt: bool = False,
        exemption_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Audit all documents in a corpus manifest dictionary."""
        docs = manifest.get("documents", [])
        results: List[FreshnessResult] = []
        for doc in docs:
            doc_id = str(doc.get("document_id", "UNKNOWN"))
            ts = doc.get(timestamp_field) or doc.get("retrieval_timestamp")
            doc_exempt = bool(doc.get("static_benchmark_exempt", static_benchmark_exempt))
            doc_reason = doc.get("exemption_reason") or exemption_reason
            results.append(
                self.evaluate_timestamp(
                    doc_id,
                    ts,
                    reference_time=reference_time,
                    static_benchmark_exempt=doc_exempt,
                    exemption_reason=doc_reason,
                )
            )

        stale_ids = [r.document_id for r in results if not r.is_fresh]
        return {
            "policy_status": self.policy_status,
            "contract_id": self.contract_id,
            "dataset_id": self.dataset_id,
            "enforcement_scope": self.enforcement_scope,
            "max_age_hours": self.max_age_hours,
            "total_documents": len(results),
            "fresh_count": sum(1 for r in results if r.is_fresh),
            "non_fresh_count": len(stale_ids),
            "non_fresh_document_ids": stale_ids,
            "requires_human_review": len(stale_ids) > 0,
            "all_fresh": len(stale_ids) == 0 and len(results) > 0,
            "results": [r.model_dump() for r in results]
        }
