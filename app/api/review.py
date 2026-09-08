
from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from pydantic import BaseModel

from app.workflow.phase3_workflow import Phase3Workflow
from app.workflow.reasoning_critic_loop import ReasoningCriticLoop
from app.workflow.hitl_reviewer import HITLReviewer
from app.workflow.reviewer_actions import ReviewerActions

router = APIRouter(
    prefix="/api/review",
    tags=["Phase 3 Review"]
)


reviewer_actions = ReviewerActions()
hitl_reviewer = HITLReviewer(
    reviewer_actions=reviewer_actions
)

workflow = None

RUNTIME_RESULT_PATH = (
    "/content/drive/MyDrive/legalmind/"
    "data/processed/application_runtime_result.json"
)

last_workflow_result = None

if Path(RUNTIME_RESULT_PATH).exists():
    with open(
        RUNTIME_RESULT_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        last_workflow_result = json.load(f)


class ReviewerActionRequest(BaseModel):
    reviewer_id: str
    rationale: str
    edited_result: dict | None = None


def set_workflow(phase3_workflow):
    global workflow
    workflow = phase3_workflow


def set_last_workflow_result(result):
    global last_workflow_result
    last_workflow_result = result


@router.get("/status")
def review_status():
    return {
        "status": "ready",
        "workflow_initialized": workflow is not None,
        "last_workflow_available": last_workflow_result is not None,
    }


@router.get("/current")
def current_review():
    if last_workflow_result is None:
        raise HTTPException(
            status_code=404,
            detail="No workflow result is available."
        )

    return last_workflow_result


@router.post("/approve")
def approve_review(request: ReviewerActionRequest):
    if last_workflow_result is None:
        raise HTTPException(
            status_code=404,
            detail="No workflow result is available."
        )

    result = hitl_reviewer.resolve(
        paused_workflow=last_workflow_result,
        action="APPROVE",
        reviewer_id=request.reviewer_id,
        rationale=request.rationale,
    )

    if result.get("status") == "FAIL":
        raise HTTPException(
            status_code=400,
            detail=result.get("reason")
        )

    return result


@router.post("/reject")
def reject_review(request: ReviewerActionRequest):
    if last_workflow_result is None:
        raise HTTPException(
            status_code=404,
            detail="No workflow result is available."
        )

    result = hitl_reviewer.resolve(
        paused_workflow=last_workflow_result,
        action="REJECT",
        reviewer_id=request.reviewer_id,
        rationale=request.rationale,
    )

    if result.get("status") == "FAIL":
        raise HTTPException(
            status_code=400,
            detail=result.get("reason")
        )

    return result


@router.post("/edit")
def edit_review(request: ReviewerActionRequest):
    if last_workflow_result is None:
        raise HTTPException(
            status_code=404,
            detail="No workflow result is available."
        )

    result = hitl_reviewer.resolve(
        paused_workflow=last_workflow_result,
        action="EDIT",
        reviewer_id=request.reviewer_id,
        rationale=request.rationale,
        edited_result=request.edited_result,
    )

    if result.get("status") == "FAIL":
        raise HTTPException(
            status_code=400,
            detail=result.get("reason")
        )

    return result


@router.get("/audit")
def get_audit_log():
    return {
        "status": "success",
        "audit": hitl_reviewer.get_audit_log(),
    }
