"""Governance & 5-Gate Decision Queue routes for CMO Agent V2.

Endpoints:
- GET /governance/recommendations (or /api/v1/recommendations)
- GET /governance/decision-queue (or /api/v1/governance/decision-queue)
- POST /governance/decisions/{decision_id}/sign-off
- GET /governance/risks (or /api/v1/governance/risks)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from evidence_rag.api.cmo_schemas import (
    AIRecommendationsResponse,
    DecisionQueueResponse,
    GateSignOffRequest,
    GateSignOffResponse,
    RiskItem,
)
from evidence_rag.api.cmo_store import CMOStore, get_cmo_store
from evidence_rag.api.dependencies import verify_tantra_token
from evidence_rag.logging_config import setup_logger

logger = setup_logger("evidence_rag.api.routes.governance")

router = APIRouter(tags=["Governance & Decision Queue"])


@router.get("/governance/recommendations", response_model=AIRecommendationsResponse)
@router.get("/recommendations", response_model=AIRecommendationsResponse, include_in_schema=False)
def get_ai_recommendations(
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> AIRecommendationsResponse:
    """Return prioritized AI recommendations with impact projections and confidence scores."""
    return store.get_recommendations()


@router.get("/governance/decision-queue", response_model=DecisionQueueResponse)
def get_decision_queue(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (AWAITING_APPROVAL, APPROVED, REJECTED)"),
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> DecisionQueueResponse:
    """Return pending decisions across the 5 Human Authority Gates:

    1. STRATEGY_GATE
    2. BUDGET_GATE
    3. BRAND_LEGAL_GATE
    4. VENDOR_CONTRACT_GATE
    5. EXECUTION_GATE
    """
    return store.get_decision_queue(status_filter=status_filter)


@router.post("/governance/decisions/{decision_id}/sign-off", response_model=GateSignOffResponse)
def sign_off_gate_decision(
    decision_id: str,
    req: GateSignOffRequest,
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> GateSignOffResponse:
    """Sign off on a pending decision in the 5-Gate Authority Queue.

    Guarantees:
    - Rejects invalid actions (must be APPROVED or REJECTED)
    - Validates human signer identity (rejects blanks, prof_evaluator, placeholders)
    - Rejects duplicate decisions on finalized records with HTTP 409 Conflict
    - Appends immutable audit entry to decision history
    """
    try:
        response = store.sign_off_decision(decision_id, req)
        logger.info(
            f"Gate decision {decision_id} successfully signed off: action={response.action}, "
            f"signer={response.signer_identity}, gate={response.gate.value}"
        )
        return response
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        msg = str(e)
        # Duplicate finalized decision triggers 409 Conflict
        status_code = status.HTTP_409_CONFLICT if "already been finalized" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=msg
        )


@router.get("/governance/risks", response_model=List[RiskItem])
def get_risks_watchlist(
    store: CMOStore = Depends(get_cmo_store),
    token: str = Depends(verify_tantra_token),
) -> List[RiskItem]:
    """Return executive risks and watchlist monitoring items."""
    forecast_and_risks = store.get_forecast_and_risks()
    return forecast_and_risks.risks
