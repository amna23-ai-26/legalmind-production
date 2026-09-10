import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["Review"])

# In-memory session state for Human-in-the-Loop review
LATEST_REVIEW_STATE: Dict[str, Any] = {
    "status": "PAUSED",
    "hitl_status": "PAUSED",
    "hitl_required": True,
    "contract_id": 1,
    "clause_id": 1,
    "risk_score": 4,
    "confidence": 0.95,
    "clause_text": "Agreement details under review...",
}


class ReviewDecisionRequest(BaseModel):
    decision: str  # "APPROVE", "REJECT", "MODIFY"
    notes: Optional[str] = ""
    modified_text: Optional[str] = None


@router.get("")
def get_review_state():
    # Return both top-level and nested structure so Next.js state checks resolve to PAUSED
    return {
        "status": "PAUSED",
        "hitl_status": "PAUSED",
        "hitl_required": True,
        "data": LATEST_REVIEW_STATE
    }


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
