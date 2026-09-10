import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["Review"])

# In-memory storage for active review state
LATEST_REVIEW_STATE: Dict[str, Any] = {
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


def set_last_workflow_result(data: Dict[str, Any]):
    """
    Helper function imported by process.py to update the review state
    when a new document is analyzed.
    """
    global LATEST_REVIEW_STATE
    if isinstance(data, dict):
        LATEST_REVIEW_STATE.update(data)
        LATEST_REVIEW_STATE["status"] = "PAUSED"
        LATEST_REVIEW_STATE["hitl_status"] = "PAUSED"
        LATEST_REVIEW_STATE["hitl_required"] = True
    return LATEST_REVIEW_STATE


class ReviewDecisionRequest(BaseModel):
    decision: str  # "APPROVE", "REJECT", "MODIFY"
    notes: Optional[str] = ""
    modified_text: Optional[str] = None


def _get_payload():
    return {
        "status": "PAUSED",
        "hitl_status": "PAUSED",
        "hitl_required": True,
        "contract_id": LATEST_REVIEW_STATE.get("contract_id", 1),
        "clause_id": LATEST_REVIEW_STATE.get("clause_id", 1),
        "risk_score": LATEST_REVIEW_STATE.get("risk_score", 4),
        "confidence": LATEST_REVIEW_STATE.get("confidence", 0.95),
        "clause_text": LATEST_REVIEW_STATE.get("clause_text", ""),
        "heading": LATEST_REVIEW_STATE.get("heading", ""),
        "data": LATEST_REVIEW_STATE,
        "items": [LATEST_REVIEW_STATE],
    }


@router.get("")
@router.get("/")
@router.get("/status")
@router.get("/current")
def get_review_state():
    return _get_payload()


@router.post("")
@router.post("/")
@router.post("/submit")
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
        "hitl_status": "COMPLETED",
        "message": f"Review recorded: {request.decision}",
        "data": LATEST_REVIEW_STATE,
    }
