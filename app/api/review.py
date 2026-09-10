import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Mount router matching main.py's global /api prefix
router = APIRouter(prefix="/review", tags=["Review"])

# State dictionary matching the exact schema expected by the frontend UI
LATEST_REVIEW_STATE: Dict[str, Any] = {
    "status": "PAUSED",
    "hitl_status": "PAUSED",
    "hitl_required": True,
    "contract_id": 1,
    "clause_id": 1,
    "risk_score": 4,
    "confidence": 0.95,
    "clause_text": "Clause 1: Scope and Delivery - Agreement details under active human review.",
    "heading": "Scope and Delivery",
    "decision": None,
    "notes": ""
}


class ReviewDecisionRequest(BaseModel):
    decision: str  # "APPROVE", "REJECT", "MODIFY"
    notes: Optional[str] = ""
    modified_text: Optional[str] = None


@router.get("")
def get_review_state():
    # Return the data payload both at top-level and inside 'data' key for UI compatibility
    response_payload = {
        **LATEST_REVIEW_STATE,
        "data": LATEST_REVIEW_STATE
    }
    return response_payload


@router.post("")
def submit_review_decision(request: ReviewDecisionRequest):
    global LATEST_REVIEW_STATE

    LATEST_REVIEW_STATE["decision"] = request.decision
    LATEST_REVIEW_STATE["notes"] = request.notes
    LATEST_REVIEW_STATE["status"] = "COMPLETED"
    LATEST_REVIEW_STATE["hitl_status"] = "COMPLETED"
    LATEST_REVIEW_STATE["hitl_required"] = False

    if request.modified_text:
        LATEST_REVIEW_STATE["clause_text"] = request.modified_text

    return {
        "status": "COMPLETED",
        "message": f"Human-in-the-loop review recorded with decision: {request.decision}",
        "data": LATEST_REVIEW_STATE
    }
