import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("legalmind")

app = FastAPI(
    title="LegalMind Intelligence Platform",
    description="Multi-Agent Legal Intelligence Platform with HITL Review & Knowledge Search",
    version="1.0.0"
)

# Enable CORS for frontend deployments (e.g. Vercel, localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "online",
        "message": "LegalMind API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Safely include routers so a failure in any single router does not crash app startup
try:
    from app.api.upload import router as upload_router
    app.include_router(upload_router)
except Exception as exc:
    logger.error(f"Failed to load upload router: {exc}")

try:
    from app.api.process import router as process_router
    app.include_router(process_router)
except Exception as exc:
    logger.error(f"Failed to load process router: {exc}")

try:
    from app.api.review import router as review_router
    app.include_router(review_router)
except Exception as exc:
    logger.error(f"Failed to load review router: {exc}")

try:
    from app.api.legal_query import router as legal_query_router
    app.include_router(legal_query_router)
except Exception as exc:
    logger.error(f"Failed to load legal_query router: {exc}")

try:
    from app.api.report import router as report_router
    app.include_router(report_router)
except Exception as exc:
    logger.error(f"Failed to load report router: {exc}")

try:
    from app.api.graph import router as graph_router
    app.include_router(graph_router)
except Exception as exc:
    logger.error(f"Failed to load graph router: {exc}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
