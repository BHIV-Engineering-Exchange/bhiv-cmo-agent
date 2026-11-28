"""Dashboard routes for CMO Agent V2 Executive Command Center.

Endpoints:
- GET /dashboard/kpis (or /api/v1/dashboard/kpis)
- GET /dashboard/strategy-progress (or /api/v1/strategy/okrs)
- GET /dashboard/campaign-portfolio (or /api/v1/campaigns)
- GET /dashboard/budget-summary (or /api/v1/budget/summary)
- GET /dashboard/forecast-and-risks (or /api/v1/analytics/forecast, /api/v1/governance/risks)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from evidence_rag.api.cmo_schemas import (
    KPISummaryResponse,
    StrategyProgressResponse,
    CampaignPortfolioResponse,
    BudgetSummaryResponse,
    ForecastAndRisksResponse,
)
from evidence_rag.api.cmo_store import CMOStore, get_cmo_store
from evidence_rag.api.dependencies import verify_tantra_token
from evidence_rag.logging_config import setup_logger

logger = setup_logger("evidence_rag.api.routes.dashboard")

router = APIRouter(tags=["Executive Dashboard"])


@router.get("/dashboard/kpis", response_model=KPISummaryResponse)
def get_dashboard_kpis(
    period: Optional[str] = Query(default="Q4-FY26", description="Reporting period (e.g. Q4-FY26, FY26, MTD)"),
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> KPISummaryResponse:
    """Return executive KPI summary cards with revenue contribution, pipeline, CAC, brand health, ROI, and NPS."""
    return store.get_kpis(period=period)


@router.get("/dashboard/strategy-progress", response_model=StrategyProgressResponse)
@router.get("/strategy/okrs", response_model=StrategyProgressResponse, include_in_schema=False)
def get_strategy_progress(
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> StrategyProgressResponse:
    """Return Strategy and OKR progress across strategic initiatives."""
    return store.get_strategy_progress()


@router.get("/dashboard/campaign-portfolio", response_model=CampaignPortfolioResponse)
@router.get("/campaigns", response_model=CampaignPortfolioResponse, include_in_schema=False)
def get_campaign_portfolio(
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> CampaignPortfolioResponse:
    """Return active campaign portfolio distribution across categories."""
    return store.get_campaign_portfolio()


@router.get("/dashboard/budget-summary", response_model=BudgetSummaryResponse)
@router.get("/budget/summary", response_model=BudgetSummaryResponse, include_in_schema=False)
def get_budget_summary(
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> BudgetSummaryResponse:
    """Return total marketing budget, commitments, spend, and forecast ROI."""
    return store.get_budget_summary()


@router.get("/dashboard/forecast-and-risks", response_model=ForecastAndRisksResponse)
@router.get("/analytics/forecast", response_model=ForecastAndRisksResponse, include_in_schema=False)
def get_forecast_and_risks(
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> ForecastAndRisksResponse:
    """Return monthly pipeline forecast, operational risk watchlist, and team capacity."""
    return store.get_forecast_and_risks()
