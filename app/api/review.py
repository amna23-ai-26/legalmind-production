import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["Review"])

# Core review state schema
CURRENT_CLAUSE: Dict[str, Any] = {
    "contract_id": 1,
    "clause_id": 1,
    "heading": "Scope and Delivery",
    "clause_text": "Clause 1: Supplier shall deliver commercial goods according to purchase orders.",
    "risk_score": 4,
    "confidence": 0.95,
    "status": "PAUSED",
    "hitl_status": "PAUSED",
    "hitl_required": True,
    "decision": None,
    "notes": "",
}


class ReviewDecisionRequest(BaseModel):
    decision: str  # "APPROVE", "REJECT", "MODIFY"
    notes: Optional[str] = ""
    modified_text: Optional[str] = None


@router.get("")
def get_review_state():
    # Return flat schema, nested 'data', and array payload for full UI compatibility
    return {
        "status": "PAUSED",
        "hitl_status": "PAUSED",
        "hitl_required": True,
        "contract_id": CURRENT_CLAUSE["contract_id"],
        "clause_id": CURRENT_CLAUSE["clause_id"],
        "risk_score": CURRENT_CLAUSE["risk_score"],
        "confidence": CURRENT_CLAUSE["confidence"],
        "clause_text": CURRENT_CLAUSE["clause_text"],
        "heading": CURRENT_CLAUSE["heading"],
        "data": CURRENT_CLAUSE,
        "items": [CURRENT_CLAUSE],
    }


@router.post("")
def submit_review_decision(request: ReviewDecisionRequest):
    global CURRENT_CLAUSE

    CURRENT_CLAUSE["decision"] = request.decision
    CURRENT_CLAUSE["notes"] = request.notes
    CURRENT_CLAUSE["status"] = "COMPLETED"
    CURRENT_CLAUSE["hitl_status"] = "COMPLETED"
    CURRENT_CLAUSE["hitl_required"] = False

    if request.modified_text:
        CURRENT_CLAUSE["clause_text"] = request.modified_text

    return {
        "status": "COMPLETED",
        "hitl_status": "COMPLETED",
        "message": f"Review recorded: {request.decision}",
        "data": CURRENT_CLAUSE,
    }
