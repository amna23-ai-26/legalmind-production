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

# Enable CORS for frontend deployments (e.g. Vercel, localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    except Exception as exc:
        err_msg = f"ERROR: {exc}\n{traceback.format_exc()}"
        router_status[name] = err_msg
        logger.error(f"Failed to load {name} router: {err_msg}")


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
    return {
        "status": "healthy",
        "routers": router_status
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
