"""Schemas for CMO Agent V2 Executive Command Center.

Covers:
- Group A: Executive Command Center (/api/v1/dashboard)
- Group B: AI Recommendations & 5-Gate Governance (/api/v1/governance)
- Group C: Omni-Search & Executive Assistant (/api/v1/cmo/chat)
"""
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# =============================================================================
# Group A: Executive Command Center Schemas
# =============================================================================

class KPIMetricItem(BaseModel):
    """Individual KPI metric with trends and formatting."""
    value: Optional[Union[float, int]] = None
    formatted: Optional[str] = None
    score: Optional[int] = None
    max_score: Optional[int] = None
    multiple: Optional[float] = None
    change_qoq_pct: Optional[float] = None
    change_pct: Optional[float] = None
    change_pts: Optional[Union[float, int]] = None
    trend: str = Field(..., description="Trend indicator: up, down, positive_reduction, neutral")


class KPISummaryResponse(BaseModel):
    """Top KPI summary response."""
    period: str = Field(..., description="Reporting period (e.g., Q4 FY26)")
    currency: str = Field(default="INR", description="Reporting currency")
    metrics: Dict[str, Any] = Field(..., description="Key executive metric cards")


class OKRInitiative(BaseModel):
    """Strategic initiative progress item."""
    name: str = Field(..., description="Initiative title")
    status: str = Field(..., description="Status: COMPLETED, IN_PROGRESS, NEXT, AT_RISK")
    progress_pct: int = Field(..., ge=0, le=100, description="Percentage of completion")


class StrategyProgressResponse(BaseModel):
    """Strategy & OKR progress tracking."""
    overall_progress_pct: int = Field(..., ge=0, le=100, description="Overall OKR progress")
    status: str = Field(default="ON_TRACK", description="High-level health: ON_TRACK, AT_RISK, BEHIND")
    initiatives: List[OKRInitiative] = Field(..., description="Key strategic initiatives")


class PortfolioCategoryDistribution(BaseModel):
    """Campaign category allocation."""
    category: str = Field(..., description="Campaign category (Demand Gen, Brand, etc.)")
    percentage: int = Field(..., ge=0, le=100, description="Percentage share of portfolio")
    count: int = Field(..., ge=0, description="Number of active campaigns")


class CampaignPortfolioResponse(BaseModel):
    """Active Campaign portfolio distribution."""
    active_campaigns_total: int = Field(..., ge=0, description="Total active campaigns")
    distribution: List[PortfolioCategoryDistribution] = Field(..., description="Category breakdown")


class BudgetSummaryResponse(BaseModel):
    """Executive budget allocation, commitments, and spend."""
    total_budget: float = Field(..., description="Total allocated budget")
    formatted_total: str = Field(..., description="Formatted total (e.g. ₹6.0 Cr)")
    committed: float = Field(..., description="Committed capital")
    committed_pct: int = Field(..., ge=0, le=100, description="Percentage committed")
    spent: float = Field(..., description="Actual spend to date")
    spent_pct: int = Field(..., ge=0, le=100, description="Percentage spent")
    remaining: float = Field(..., description="Remaining uncommitted capital")
    forecast_roi: str = Field(..., description="Projected marketing return multiple (e.g. 5.1x)")


class MonthlyForecastItem(BaseModel):
    """Forecast projection per month."""
    month: str = Field(..., description="Month name (e.g. Nov, Dec)")
    revenue_target_cr: float = Field(..., description="Revenue target in Crores")
    pipeline_weighted_cr: float = Field(..., description="Weighted pipeline projection in Crores")


class RiskItem(BaseModel):
    """Monitored executive risk item."""
    id: str = Field(..., description="Risk identifier")
    risk: str = Field(..., description="Risk description")
    severity: str = Field(..., description="Severity level: HIGH, MEDIUM, LOW")


class TeamCapacity(BaseModel):
    """Marketing and agency operational bandwidth."""
    capacity_pct: int = Field(..., ge=0, le=100, description="Capacity utilization percentage")
    team_count: int = Field(..., ge=0, description="Internal team headcount")
    agencies_count: int = Field(..., ge=0, description="Engaged partner agencies")
    active_projects: int = Field(..., ge=0, description="Active running projects")


class ForecastAndRisksResponse(BaseModel):
    """Revenue pipeline forecast and operational risk watchlist."""
    monthly_forecast: List[MonthlyForecastItem] = Field(..., description="Monthly pipeline projections")
    risks: List[RiskItem] = Field(..., description="Active risk watchlist")
    team_capacity: TeamCapacity = Field(..., description="Team & agency bandwidth")


# =============================================================================
# Group B: AI Recommendations & 5-Gate Governance Schemas
# =============================================================================

class GovernanceGate(str, Enum):
    """The 5 Human Authority Gates for CMO Decision Governance."""
    STRATEGY_GATE = "STRATEGY_GATE"
    BUDGET_GATE = "BUDGET_GATE"
    BRAND_LEGAL_GATE = "BRAND_LEGAL_GATE"
    VENDOR_CONTRACT_GATE = "VENDOR_CONTRACT_GATE"
    EXECUTION_GATE = "EXECUTION_GATE"


class DecisionStatus(str, Enum):
    """Decision state machine status."""
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AIRecommendation(BaseModel):
    """Prioritized AI-generated strategic recommendation."""
    id: str = Field(..., description="Recommendation ID (e.g. REC-001)")
    priority: int = Field(..., ge=1, description="Relative priority order (1 is highest)")
    title: str = Field(..., description="Actionable title")
    impact: str = Field(..., description="Quantified business impact")
    confidence_level: str = Field(..., description="Confidence label (High Confidence, Medium Confidence)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Statistical confidence score")
    action_type: str = Field(..., description="Action category (CAMPAIGN_SCALE, GTM_APPROVAL, BUDGET_REALLOCATION)")


class AIRecommendationsResponse(BaseModel):
    """List of prioritized AI recommendations."""
    recommendations: List[AIRecommendation] = Field(..., description="Prioritized recommendations")


class DecisionAuditEntry(BaseModel):
    """Immutable entry in decision signing history."""
    action: str = Field(..., description="APPROVED or REJECTED")
    signer_identity: str = Field(..., description="Identity of signer")
    signer_role: str = Field(..., description="Role of signer")
    notes: Optional[str] = Field(None, description="Sign-off notes or justification")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionQueueItem(BaseModel):
    """Pending decision item in the 5-Gate Authority Queue."""
    decision_id: str = Field(..., description="Decision identifier (e.g. DEC-BUD-001)")
    gate: GovernanceGate = Field(..., description="One of the 5 Governance Gates")
    title: str = Field(..., description="Decision title")
    requested_by: str = Field(..., description="Originating team or role")
    amount: Optional[float] = Field(None, description="Associated monetary spend if applicable")
    status: DecisionStatus = Field(default=DecisionStatus.AWAITING_APPROVAL, description="Current decision status")
    requires_role: List[str] = Field(..., description="Authorized roles permitted to sign off")
    history: List[DecisionAuditEntry] = Field(default_factory=list, description="Immutable audit log")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signed_at: Optional[str] = Field(None, description="ISO timestamp when signed")


class DecisionQueueResponse(BaseModel):
    """Decision queue listing response."""
    pending_count: int = Field(..., ge=0, description="Number of items awaiting approval")
    queue: List[DecisionQueueItem] = Field(..., description="Pending decision items")


class GateSignOffRequest(BaseModel):
    """Request payload to approve or reject a decision queue item."""
    action: str = Field(..., description="APPROVED or REJECTED")
    signer_identity: str = Field(..., min_length=3, description="Signer email or unique corporate identity")
    signer_role: str = Field(..., min_length=2, description="Signer title/role (e.g. Chief Marketing Officer)")
    notes: Optional[str] = Field(default=None, description="Audit justification or sign-off notes")


class GateSignOffResponse(BaseModel):
    """Response returned upon signing off a decision queue item."""
    decision_id: str
    status: DecisionStatus
    action: str
    signer_identity: str
    signer_role: str
    notes: Optional[str] = None
    signed_at: str
    gate: GovernanceGate
    title: str
    audit_entry: DecisionAuditEntry
    pending_count_remaining: int


# =============================================================================
# Group C: Omni-Search & Executive Assistant Schemas
# =============================================================================

class GroundedSource(BaseModel):
    """Source item supporting the executive answer."""
    source: str = Field(..., description="Data feed or document identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance or certainty score")


class CMOChatRequest(BaseModel):
    """Omni-search and executive conversational query."""
    query: str = Field(..., min_length=3, description="Executive question across metrics and policies")
    include_metrics: Optional[bool] = Field(default=True, description="Whether to include live metric lookups")
    include_citations: Optional[bool] = Field(default=True, description="Whether to include grounded sources")


class CMOChatResponse(BaseModel):
    """Synthesized executive answer with grounding and suggested actions."""
    answer: str = Field(..., description="Concise, synthesized executive answer")
    grounded_sources: List[GroundedSource] = Field(default_factory=list, description="Supporting feeds and documents")
    suggested_actions: List[str] = Field(default_factory=list, description="Next actionable recommendations")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
