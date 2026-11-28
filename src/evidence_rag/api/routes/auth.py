"""Authentication and session negotiation routes for CMO Agent Path B."""
from fastapi import APIRouter
from evidence_rag.api.config import api_settings

router = APIRouter(tags=["Authentication & Session"])


@router.get("/auth/session")
def get_auth_session():
    """Return session authentication status and ephemeral development token when non-strict."""
    if not api_settings.auth_enabled:
        return {
            "auth_enabled": False,
            "token": None,
            "mode": "auth_disabled",
            "message": "Authentication is disabled in API settings."
        }

    if api_settings.auth_strict_rs256:
        return {
            "auth_enabled": True,
            "token": None,
            "mode": "strict_rs256_required",
            "message": "Strict TANTRA RS256 token verification is active. Token must be supplied manually."
        }

    return {
        "auth_enabled": True,
        "token": "cmo-session-dev-token",
        "mode": "development_session",
        "message": "Ephemeral local development token provisioned."
    }
