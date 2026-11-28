"""REST Route modules for CMO Agent API."""
from evidence_rag.api.routes.health import router as health_router
from evidence_rag.api.routes.query import router as query_router
from evidence_rag.api.routes.proposals import router as proposals_router
from evidence_rag.api.routes.auth import router as auth_router
from evidence_rag.api.routes.dashboard import router as dashboard_router
from evidence_rag.api.routes.governance import router as governance_router
from evidence_rag.api.routes.cmo_chat import router as cmo_chat_router

__all__ = [
    "health_router",
    "query_router",
    "proposals_router",
    "auth_router",
    "dashboard_router",
    "governance_router",
    "cmo_chat_router",
]
