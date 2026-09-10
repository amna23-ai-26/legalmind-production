import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.workflow.reviewer_actions import ReviewerActions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["Review"])

# Single in-memory audit log, shared by every action route below.
reviewer_actions = ReviewerActions()

# Demo fallback state. Only shown until a real document has been analyzed
# via POST /api/process, at which point set_last_workflow_result() below
# replaces it with the actual reasoning/risk/hitl/explainability result.
LATEST_REVIEW_STATE: Dict[str, Any] = {
    "contract_id": 1,
    "clause_id": 1,
    "heading": "Scope and Delivery",
    "clause_text": "Clause 1.1: Supplier shall deliver commercial goods according to purchase orders issued by Purchaser. Time is of the essence in this Agreement.",
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
    Called by app.api.process once a real document has been analyzed.

    `data` is the full workflow result (reasoning_critic, risk_findings,
    hitl, explainability, ...). Previously this only merged those nested
    keys into LATEST_REVIEW_STATE without ever updating the flat
    contract_id/clause_id/clause_text/heading fields (those keys don't
    exist at the top level of the workflow result), so the API kept
    serving its hardcoded init values forever. We now derive the flat
    fields from the nested reasoning result so they track the real
    analysis.
    """
    global LATEST_REVIEW_STATE
    if not isinstance(data, dict):
        return LATEST_REVIEW_STATE

    LATEST_REVIEW_STATE.update(data)

    reasoning_result = (
        (LATEST_REVIEW_STATE.get("reasoning_critic") or {}).get("reasoning_result") or {}
    )

    if reasoning_result.get("contract_id") is not None:
        LATEST_REVIEW_STATE["contract_id"] = reasoning_result["contract_id"]
    if reasoning_result.get("clause_id") is not None:
        LATEST_REVIEW_STATE["clause_id"] = reasoning_result["clause_id"]
    if reasoning_result.get("clause_text"):
        LATEST_REVIEW_STATE["clause_text"] = reasoning_result["clause_text"]
    if reasoning_result.get("clause_heading"):
        LATEST_REVIEW_STATE["heading"] = reasoning_result["clause_heading"]

    hitl = LATEST_REVIEW_STATE.get("hitl") or {}
    if hitl.get("document_risk_score") is not None:
        LATEST_REVIEW_STATE["risk_score"] = hitl["document_risk_score"]

    confidence_score = (
        (LATEST_REVIEW_STATE.get("explainability") or {}).get("confidence") or {}
    ).get("score")
    if confidence_score is not None:
        LATEST_REVIEW_STATE["confidence"] = confidence_score

    hitl_required = LATEST_REVIEW_STATE.get("hitl_required", True)
    LATEST_REVIEW_STATE["status"] = "PAUSED" if hitl_required else "COMPLETED"
    LATEST_REVIEW_STATE["hitl_status"] = LATEST_REVIEW_STATE["status"]

    return LATEST_REVIEW_STATE


class ReviewDecisionRequest(BaseModel):
    decision: Optional[str] = None
    reviewer_id: Optional[str] = "dashboard-reviewer"
    rationale: Optional[str] = ""
    notes: Optional[str] = ""
    modified_text: Optional[str] = None
    edited_result: Optional[Dict[str, Any]] = None


def _get_payload():
    """
    Build the /api/review/current response.

    Previously this returned only a handful of flat fields, so the rich
    workflow result (reasoning_critic, risk_findings, hitl,
    explainability) stored in LATEST_REVIEW_STATE was only reachable via
    `data`/`items`, never at the top level where the frontend reads it
    (result.reasoning_critic.reasoning_result, result.risk_findings,
    result.hitl, result.explainability). That mismatch is why the UI
    always fell back to its hardcoded Contract #1 / Clause #17 demo
    values even after a real document was analyzed. Spreading
    LATEST_REVIEW_STATE onto the payload fixes that.
    """
    reasoning_result = (
        (LATEST_REVIEW_STATE.get("reasoning_critic") or {}).get("reasoning_result") or {}
    )

    payload = dict(LATEST_REVIEW_STATE)
    payload.update(
        {
            "status": LATEST_REVIEW_STATE.get("status", "PAUSED"),
            "hitl_status": LATEST_REVIEW_STATE.get("hitl_status", "PAUSED"),
            "hitl_required": LATEST_REVIEW_STATE.get("hitl_required", True),
            "contract_id": reasoning_result.get(
                "contract_id", LATEST_REVIEW_STATE.get("contract_id", 1)
            ),
            "clause_id": reasoning_result.get(
                "clause_id", LATEST_REVIEW_STATE.get("clause_id", 1)
            ),
            "risk_score": LATEST_REVIEW_STATE.get("risk_score", 4),
            "confidence": LATEST_REVIEW_STATE.get("confidence", 0.95),
            "clause_text": reasoning_result.get(
                "clause_text",
                LATEST_REVIEW_STATE.get("clause_text", "Clause text available for review."),
            ),
            "heading": reasoning_result.get(
                "clause_heading", LATEST_REVIEW_STATE.get("heading", "Clause Review")
            ),
            "data": LATEST_REVIEW_STATE,
            "items": [LATEST_REVIEW_STATE],
        }
    )
    return payload


@router.get("")
@router.get("/")
@router.get("/status")
@router.get("/current")
def get_review_state():
    return _get_payload()


@router.get("/audit")
def get_audit_log():
    # ReviewerActions already maintains an immutable audit trail; this
    # route was missing entirely, so the frontend's "Immutable Reviewer
    # Activity" panel always silently showed zero entries.
    return {"audit": reviewer_actions.get_audit_log()}


def _submit(action_upper: str, request: ReviewDecisionRequest):
    global LATEST_REVIEW_STATE

    reviewer_id = request.reviewer_id or "dashboard-reviewer"
    rationale = request.rationale or request.notes or f"Reviewer selected {action_upper}."

    try:
        if action_upper == "EDIT":
            record = reviewer_actions.edit(
                reviewer_id=reviewer_id,
                rationale=rationale,
                edited_result=request.edited_result,
                workflow_state=LATEST_REVIEW_STATE,
            )
        elif action_upper == "APPROVE":
            record = reviewer_actions.approve(
                reviewer_id=reviewer_id,
                rationale=rationale,
                workflow_state=LATEST_REVIEW_STATE,
            )
        elif action_upper == "REJECT":
            record = reviewer_actions.reject(
                reviewer_id=reviewer_id,
                rationale=rationale,
                workflow_state=LATEST_REVIEW_STATE,
            )
        else:
            raise HTTPException(status_code=404, detail=f"Unknown review action: {action_upper}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    LATEST_REVIEW_STATE["decision"] = action_upper
    LATEST_REVIEW_STATE["notes"] = rationale
    LATEST_REVIEW_STATE["status"] = "COMPLETED"
    LATEST_REVIEW_STATE["hitl_status"] = "COMPLETED"
    LATEST_REVIEW_STATE["hitl_required"] = False

    if request.modified_text:
        LATEST_REVIEW_STATE["clause_text"] = request.modified_text

    return {
        "status": "COMPLETED",
        "hitl_status": "COMPLETED",
        "message": f"Review recorded: {action_upper}",
        "audit_record": record,
        "data": LATEST_REVIEW_STATE,
    }


# Dedicated action routes. These are what the frontend actually calls
# (POST /api/review/{approve|edit|reject}) — they previously 404'd
# because only the generic "" / "/" / "/submit" routes existed below.
@router.post("/approve")
def approve_review(request: ReviewDecisionRequest):
    return _submit("APPROVE", request)


@router.post("/reject")
def reject_review(request: ReviewDecisionRequest):
    return _submit("REJECT", request)


@router.post("/edit")
def edit_review(request: ReviewDecisionRequest):
    return _submit("EDIT", request)


@router.post("")
@router.post("/")
@router.post("/submit")
def submit_review_decision(request: ReviewDecisionRequest):
    action_upper = (request.decision or "APPROVE").upper()
    return _submit(action_upper, request)
