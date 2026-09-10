import os
import logging
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("legalmind")

app = FastAPI(
    title="LegalMind Intelligence Platform",
    description="Multi-Agent Legal Intelligence Platform with HITL Review & Knowledge Search",
    version="1.0.0"
)

# Explicit allowed origins list
allowed_origins = [
    "https://legalmind-production.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Fallback for dynamic preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router_status = {}


def load_router(name, import_fn):
    try:
        router = import_fn()
        app.include_router(router)
        router_status[name] = "LOADED"
        logger.info(f"Successfully loaded {name} router")
    except Exception as exc:
        err_msg = f"ERROR: {exc}\n{traceback.format_exc()}"
        router_status[name] = err_msg
        logger.error(f"Failed to load {name} router: {err_msg}")


# Dynamic sub-router imports
load_router("upload", lambda: __import__("app.api.upload", fromlist=["router"]).router)
load_router("process", lambda: __import__("app.api.process", fromlist=["router"]).router)
load_router("review", lambda: __import__("app.api.review", fromlist=["router"]).router)
load_router("legal_query", lambda: __import__("app.api.legal_query", fromlist=["router"]).router)
load_router("report", lambda: __import__("app.api.report", fromlist=["router"]).router)
load_router("graph", lambda: __import__("app.api.graph", fromlist=["router"]).router)


@app.get("/")
def root():
    return {
        "status": "online",
        "message": "LegalMind API is running",
        "version": "1.0.0",
        "routers": router_status
    }


@app.get("/health")
def health():
    has_errors = any("ERROR" in str(val) for val in router_status.values())
    return {
        "status": "degraded" if has_errors else "healthy",
        "routers": router_status
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
