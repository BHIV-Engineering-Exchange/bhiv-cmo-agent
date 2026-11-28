"""Persistent store and aggregator for CMO Agent V2 Executive Command Center.

Manages:
- Executive KPIs, OKRs, Campaign Portfolio, Budget Summary, Forecast & Risks
- AI Recommendations
- 5-Gate Governance Decision Queue (thread-safe, disk-persisted)
- Metric snapshot lookups for Omni-Search assistant
"""
import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from evidence_rag.api.cmo_schemas import (
    KPISummaryResponse,
    StrategyProgressResponse,
    OKRInitiative,
    CampaignPortfolioResponse,
    PortfolioCategoryDistribution,
    BudgetSummaryResponse,
    ForecastAndRisksResponse,
    MonthlyForecastItem,
    RiskItem,
    TeamCapacity,
    AIRecommendation,
    AIRecommendationsResponse,
    DecisionQueueItem,
    DecisionQueueResponse,
    GovernanceGate,
    DecisionStatus,
    DecisionAuditEntry,
    GateSignOffRequest,
    GateSignOffResponse,
)
from evidence_rag.logging_config import setup_logger

logger = setup_logger("evidence_rag.api.cmo_store")


class CMOStore:
    """Thread-safe persistent store and metric aggregator."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # Default to data/governance in project root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.data_dir = base_dir / "data" / "governance"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.data_dir / "decision_queue.json"
        self._lock = threading.RLock()
        self._init_decision_queue()

    # -------------------------------------------------------------------------
    # Group A: Executive Command Center Data Aggregation
    # -------------------------------------------------------------------------

    def get_kpis(self, period: Optional[str] = None) -> KPISummaryResponse:
        """Return executive KPI cards with formatted INR values, QoQ changes, and trends."""
        norm_period = (period or "Q4-FY26").replace("-", " ").strip().upper()
        if "Q4" in norm_period:
            period_label = "Q4 FY26"
            metrics = {
                "marketing_contribution_revenue": {
                    "value": 284000000,
                    "formatted": "₹28.4 Cr",
                    "change_qoq_pct": 15.0,
                    "trend": "up"
                },
                "qualified_pipeline": {
                    "value": 967000000,
                    "formatted": "₹96.7 Cr",
                    "change_pct": 24.0,
                    "trend": "up"
                },
                "brand_health_index": {
                    "score": 82,
                    "max_score": 100,
                    "change_pts": 6,
                    "trend": "up"
                },
                "cac": {
                    "value": 14200,
                    "formatted": "₹14,200",
                    "change_pct": -12.0,
                    "trend": "positive_reduction"
                },
                "marketing_roi": {
                    "multiple": 4.8,
                    "change_pts": 0.9,
                    "trend": "up"
                },
                "customer_nps": {
                    "score": 56,
                    "change_pts": 8,
                    "trend": "up"
                }
            }
        elif "FY26" in norm_period:
            period_label = "FY26 (Full Year)"
            metrics = {
                "marketing_contribution_revenue": {
                    "value": 1050000000,
                    "formatted": "₹105.0 Cr",
                    "change_qoq_pct": 28.5,
                    "trend": "up"
                },
                "qualified_pipeline": {
                    "value": 3400000000,
                    "formatted": "₹340.0 Cr",
                    "change_pct": 32.0,
                    "trend": "up"
                },
                "brand_health_index": {
                    "score": 84,
                    "max_score": 100,
                    "change_pts": 9,
                    "trend": "up"
                },
                "cac": {
                    "value": 13800,
                    "formatted": "₹13,800",
                    "change_pct": -15.0,
                    "trend": "positive_reduction"
                },
                "marketing_roi": {
                    "multiple": 5.1,
                    "change_pts": 1.2,
                    "trend": "up"
                },
                "customer_nps": {
                    "score": 60,
                    "change_pts": 12,
                    "trend": "up"
                }
            }
        else:
            period_label = norm_period
            metrics = {
                "marketing_contribution_revenue": {
                    "value": 92000000,
                    "formatted": "₹9.2 Cr",
                    "change_qoq_pct": 8.0,
                    "trend": "up"
                },
                "qualified_pipeline": {
                    "value": 310000000,
                    "formatted": "₹31.0 Cr",
                    "change_pct": 14.0,
                    "trend": "up"
                },
                "brand_health_index": {
                    "score": 81,
                    "max_score": 100,
                    "change_pts": 4,
                    "trend": "up"
                },
                "cac": {
                    "value": 14500,
                    "formatted": "₹14,500",
                    "change_pct": -8.0,
                    "trend": "positive_reduction"
                },
                "marketing_roi": {
                    "multiple": 4.6,
                    "change_pts": 0.6,
                    "trend": "up"
                },
                "customer_nps": {
                    "score": 55,
                    "change_pts": 5,
                    "trend": "up"
                }
            }

        return KPISummaryResponse(
            period=period_label,
            currency="INR",
            metrics=metrics
        )

    def get_strategy_progress(self) -> StrategyProgressResponse:
        """Return OKR and strategic initiative progress."""
        initiatives = [
            OKRInitiative(name="Market expansion (India - Phase 1)", status="COMPLETED", progress_pct=100),
            OKRInitiative(name="Brand repositioning rollout", status="COMPLETED", progress_pct=100),
            OKRInitiative(name="Demand generation scale-up", status="IN_PROGRESS", progress_pct=65),
            OKRInitiative(name="Product GTM - AI Suite", status="NEXT", progress_pct=20),
            OKRInitiative(name="Customer retention program", status="NEXT", progress_pct=10),
        ]
        return StrategyProgressResponse(
            overall_progress_pct=76,
            status="ON_TRACK",
            initiatives=initiatives
        )

    def get_campaign_portfolio(self) -> CampaignPortfolioResponse:
        """Return active campaign portfolio distribution across categories."""
        distribution = [
            PortfolioCategoryDistribution(category="Demand Gen", percentage=34, count=4),
            PortfolioCategoryDistribution(category="Brand", percentage=21, count=3),
            PortfolioCategoryDistribution(category="Product / GTM", percentage=18, count=2),
            PortfolioCategoryDistribution(category="Partner / Channel", percentage=11, count=1),
            PortfolioCategoryDistribution(category="Retention / CX", percentage=10, count=1),
            PortfolioCategoryDistribution(category="Others", percentage=6, count=1),
        ]
        return CampaignPortfolioResponse(
            active_campaigns_total=12,
            distribution=distribution
        )

    def get_budget_summary(self) -> BudgetSummaryResponse:
        """Return total budget, commitments, spend, remaining, and ROI."""
        return BudgetSummaryResponse(
            total_budget=60000000.0,
            formatted_total="₹6.0 Cr",
            committed=42000000.0,
            committed_pct=70,
            spent=28000000.0,
            spent_pct=47,
            remaining=18000000.0,
            forecast_roi="5.1x"
        )

    def get_forecast_and_risks(self) -> ForecastAndRisksResponse:
        """Return monthly revenue/pipeline forecasts, risk watchlist, and capacity."""
        monthly_forecast = [
            MonthlyForecastItem(month="Nov", revenue_target_cr=80.0, pipeline_weighted_cr=95.0),
            MonthlyForecastItem(month="Dec", revenue_target_cr=90.0, pipeline_weighted_cr=105.0),
            MonthlyForecastItem(month="Jan", revenue_target_cr=100.0, pipeline_weighted_cr=115.0),
            MonthlyForecastItem(month="Feb", revenue_target_cr=110.0, pipeline_weighted_cr=125.0),
            MonthlyForecastItem(month="Mar", revenue_target_cr=120.0, pipeline_weighted_cr=140.0),
        ]
        risks = [
            RiskItem(id="RSK-01", risk="Channel cost inflation (+15%)", severity="MEDIUM"),
            RiskItem(id="RSK-02", risk="Competitor price campaign", severity="HIGH"),
            RiskItem(id="RSK-03", risk="Content bandwidth (team) gap", severity="MEDIUM"),
        ]
        team_capacity = TeamCapacity(
            capacity_pct=82,
            team_count=14,
            agencies_count=3,
            active_projects=27
        )
        return ForecastAndRisksResponse(
            monthly_forecast=monthly_forecast,
            risks=risks,
            team_capacity=team_capacity
        )

    # -------------------------------------------------------------------------
    # Group B: AI Recommendations & 5-Gate Governance Queue
    # -------------------------------------------------------------------------

    def get_recommendations(self) -> AIRecommendationsResponse:
        """Return prioritized AI recommendations with quantified impact and confidence."""
        recs = [
            AIRecommendation(
                id="REC-001",
                priority=1,
                title="Scale LinkedIn + Industry Outreach",
                impact="₹18-24 Cr pipeline potential",
                confidence_level="High Confidence",
                confidence_score=0.87,
                action_type="CAMPAIGN_SCALE"
            ),
            AIRecommendation(
                id="REC-002",
                priority=2,
                title="Approve AI Product GTM Plan",
                impact="Launch readiness at 82%",
                confidence_level="Medium Confidence",
                confidence_score=0.74,
                action_type="GTM_APPROVAL"
            ),
            AIRecommendation(
                id="REC-003",
                priority=3,
                title="Reallocate 10% budget from low-ROI channels",
                impact="Expected ROI uplift: +0.6x",
                confidence_level="High Confidence",
                confidence_score=0.88,
                action_type="BUDGET_REALLOCATION"
            ),
        ]
        return AIRecommendationsResponse(recommendations=recs)

    def _default_queue_items(self) -> List[Dict[str, Any]]:
        """Default 5-Gate decision queue seed data."""
        return [
            {
                "decision_id": "DEC-BUD-001",
                "gate": GovernanceGate.BUDGET_GATE.value,
                "title": "Budget reallocation (₹60 L)",
                "requested_by": "Performance Marketing Lead",
                "amount": 6000000.0,
                "status": DecisionStatus.AWAITING_APPROVAL.value,
                "requires_role": ["CMO", "Finance Director"],
                "history": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "signed_at": None
            },
            {
                "decision_id": "DEC-GTM-002",
                "gate": GovernanceGate.STRATEGY_GATE.value,
                "title": "Product launch (AI Suite) - Go/No-Go",
                "requested_by": "GTM Director",
                "amount": None,
                "status": DecisionStatus.AWAITING_APPROVAL.value,
                "requires_role": ["CMO"],
                "history": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "signed_at": None
            },
            {
                "decision_id": "DEC-VND-003",
                "gate": GovernanceGate.VENDOR_CONTRACT_GATE.value,
                "title": "Agency contract renewal (Q1-Q4 FY27)",
                "requested_by": "Brand Operations Lead",
                "amount": None,
                "status": DecisionStatus.AWAITING_APPROVAL.value,
                "requires_role": ["CMO", "Legal Head"],
                "history": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "signed_at": None
            },
            {
                "decision_id": "DEC-BRD-004",
                "gate": GovernanceGate.BRAND_LEGAL_GATE.value,
                "title": "Brand communication (sensitive PR)",
                "requested_by": "Corporate Communications",
                "amount": None,
                "status": DecisionStatus.AWAITING_APPROVAL.value,
                "requires_role": ["CMO"],
                "history": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "signed_at": None
            }
        ]

    def _init_decision_queue(self) -> None:
        """Initialize the decision queue JSON file if missing or empty."""
        with self._lock:
            if not self.queue_file.exists() or self.queue_file.stat().st_size == 0:
                defaults = self._default_queue_items()
                self._write_queue_file(defaults)

    def _read_queue_file(self) -> List[Dict[str, Any]]:
        """Read raw queue items from disk."""
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to read decision queue from {self.queue_file}: {e}")
            return self._default_queue_items()

    def _write_queue_file(self, items: List[Dict[str, Any]]) -> None:
        """Atomically persist queue items to disk."""
        temp_file = self.queue_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2)
            temp_file.replace(self.queue_file)
        except Exception as e:
            logger.error(f"Failed to write decision queue to {self.queue_file}: {e}")
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            raise

    def get_decision_queue(self, status_filter: Optional[str] = None) -> DecisionQueueResponse:
        """Return decision items and count of pending decisions."""
        with self._lock:
            raw_items = self._read_queue_file()

        parsed: List[DecisionQueueItem] = []
        for raw in raw_items:
            try:
                item = DecisionQueueItem(**raw)
                if status_filter:
                    if item.status.value != status_filter.upper():
                        continue
                parsed.append(item)
            except Exception as e:
                logger.warning(f"Skipping malformed decision item: {e}")

        pending_count = sum(1 for item in parsed if item.status == DecisionStatus.AWAITING_APPROVAL)
        return DecisionQueueResponse(
            pending_count=pending_count,
            queue=parsed
        )

    def get_decision_by_id(self, decision_id: str) -> Optional[DecisionQueueItem]:
        """Fetch a single decision queue item by ID."""
        with self._lock:
            raw_items = self._read_queue_file()
            for raw in raw_items:
                if raw.get("decision_id") == decision_id:
                    return DecisionQueueItem(**raw)
        return None

    def sign_off_decision(self, decision_id: str, req: GateSignOffRequest) -> GateSignOffResponse:
        """Sign off on a decision item with state machine validation and audit log."""
        action_clean = req.action.strip().upper()
        if action_clean not in ("APPROVED", "REJECTED"):
            raise ValueError(f"Invalid sign-off action '{req.action}'. Must be 'APPROVED' or 'REJECTED'.")

        # Identity validation (QA-001 equivalent: prevent empty or placeholder identity)
        signer_clean = req.signer_identity.strip()
        if not signer_clean or len(signer_clean) < 3:
            raise ValueError("Field 'signer_identity' must be at least 3 characters.")
        if signer_clean.lower() in ("prof_evaluator", "anonymous", "default", "none"):
            raise ValueError(f"Placeholder signer identity '{req.signer_identity}' is prohibited.")

        role_clean = req.signer_role.strip()
        if not role_clean or len(role_clean) < 2:
            raise ValueError("Field 'signer_role' must be specified.")

        with self._lock:
            raw_items = self._read_queue_file()
            target_idx = None
            for idx, raw in enumerate(raw_items):
                if raw.get("decision_id") == decision_id:
                    target_idx = idx
                    break

            if target_idx is None:
                raise KeyError(f"Decision '{decision_id}' not found in governance queue.")

            target = raw_items[target_idx]
            current_status = target.get("status")

            # Duplicate decision check -> 409 Conflict
            if current_status in (DecisionStatus.APPROVED.value, DecisionStatus.REJECTED.value):
                raise ValueError(
                    f"Decision '{decision_id}' has already been finalized with status '{current_status}'."
                )

            # Update decision status and audit history
            now_iso = datetime.now(timezone.utc).isoformat()
            new_status = DecisionStatus.APPROVED if action_clean == "APPROVED" else DecisionStatus.REJECTED

            audit_entry = DecisionAuditEntry(
                action=action_clean,
                signer_identity=signer_clean,
                signer_role=role_clean,
                notes=req.notes,
                timestamp=now_iso
            )

            history = target.get("history") or []
            history.append(audit_entry.model_dump())

            target["status"] = new_status.value
            target["signed_at"] = now_iso
            target["history"] = history
            raw_items[target_idx] = target

            self._write_queue_file(raw_items)

            # Compute remaining pending
            remaining_pending = sum(
                1 for r in raw_items if r.get("status") == DecisionStatus.AWAITING_APPROVAL.value
            )

            return GateSignOffResponse(
                decision_id=decision_id,
                status=new_status,
                action=action_clean,
                signer_identity=signer_clean,
                signer_role=role_clean,
                notes=req.notes,
                signed_at=now_iso,
                gate=GovernanceGate(target["gate"]),
                title=target["title"],
                audit_entry=audit_entry,
                pending_count_remaining=remaining_pending
            )

    def reset_queue(self) -> None:
        """Reset decision queue to initial defaults (used in test fixtures)."""
        with self._lock:
            defaults = self._default_queue_items()
            self._write_queue_file(defaults)


# Singleton instance
_cmo_store_instance: Optional[CMOStore] = None


def get_cmo_store() -> CMOStore:
    """Return singleton instance of CMOStore."""
    global _cmo_store_instance
    if _cmo_store_instance is None:
        _cmo_store_instance = CMOStore()
    return _cmo_store_instance
