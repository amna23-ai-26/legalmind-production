from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from app.workflow.phase3_workflow import Phase3Workflow
from app.workflow.reasoning_critic_loop import ReasoningCriticLoop
from app.workflow.hitl_reviewer import HITLReviewer
from app.workflow.reviewer_actions import ReviewerActions
from app.config import get_runtime_result_path

router = APIRouter(
    prefix="/api/review",
    tags=["Phase 3 Review"]
)


reviewer_actions = ReviewerActions()
hitl_reviewer = HITLReviewer(
    reviewer_actions=reviewer_actions
)

workflow = None

DEFAULT_INITIAL_REVIEW = {
    "document_id": "ready",
    "workflow_status": "READY",
    "metadata": {
        "corpus": "pakistan_statutes",
        "jurisdiction": "Pakistan"
    },
    "risk_findings": [],
    "clauses": [],
    "hitl": {
        "status": "READY",
        "document_risk_score": 0,
        "reason": "Ready for document analysis."
    },
    "reasoning_critic": {
        "reasoning_result": {
            "contract_id": 1,
            "clause_id": 1,
            "clause_heading": "Upload a Document to Begin Review",
            "clause_text": "Please upload a contract document (PDF or DOCX) in the Analyze Document view to begin automated risk analysis and human review.",
            "risk": {"score": 0, "level": "Low"},
            "legal_assessment": "System is ready for contract upload.",
            "negotiation_recommendations": ["Upload a contract document to generate legal recommendations."],
            "supporting_evidence": {"case_law": []}
        },
        "critic_result": {
            "status": "READY",
            "citation_check": {"passed": True},
            "consistency_check": {"passed": True}
        }
    },
    "explainability": {
        "confidence": {
            "score": 1.0,
            "retrieval_similarity": 1.0,
            "critic_score": 1.0,
            "self_consistency": {"n": 3, "score": 1.0}
        },
        "evidence_graph": {"nodes": [], "edges": []}
    }
}

last_workflow_result = None

runtime_path = get_runtime_result_path()
if runtime_path.exists():
    try:
        with open(runtime_path, "r", encoding="utf-8") as f:
            last_workflow_result = json.load(f)
    except Exception:
        last_workflow_result = None


class ReviewerActionRequest(BaseModel):
    reviewer_id: str
    rationale: str
    edited_result: Optional[dict] = None


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
        return DEFAULT_INITIAL_REVIEW

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
