from fastapi import FastAPI

from app.api.upload import router as upload_router
from app.api.graph import router as graph_router
from app.api.review import router as review_router
from app.api.process import router as process_router
from app.api.legal_query import router as legal_query_router


app = FastAPI(
    title="LegalMind Phase 1 + Phase 2",
    description="Document Agent + Risk Agent MVP with Knowledge Graph",
    version="1.0.0"
)


# ============================================================
# PHASE 1 — DOCUMENT API
# ============================================================

app.include_router(
    upload_router
)


# ============================================================
# PHASE 2 — KNOWLEDGE GRAPH API
# ============================================================

app.include_router(
    graph_router
)


# ============================================================
# PHASE 3 — REVIEW API
# ============================================================

app.include_router(
    review_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "LegalMind API is running",
        "phase": "Phase 1 + Phase 2"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

app.include_router(
    process_router
)

app.include_router(
    legal_query_router
)
