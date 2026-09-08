
from copy import deepcopy

from app.workflow.reviewer_actions import ReviewerActions


class HITLReviewer:
    """
    Phase 3 HITL Reviewer Coordinator v1.

    Resolves a PAUSED workflow through:
        APPROVE
        REJECT
        EDIT

    ReviewerActions remains the sole audit-log writer.
    """

    def __init__(self, reviewer_actions=None):
        self.reviewer_actions = (
            reviewer_actions
            if reviewer_actions is not None
            else ReviewerActions()
        )

    def resolve(
        self,
        paused_workflow,
        action,
        reviewer_id,
        rationale,
        edited_result=None,
    ):
        if not isinstance(paused_workflow, dict):
            return self._failure(
                "paused_workflow must be a dictionary"
            )

        if paused_workflow.get("paused") is not True:
            return self._failure(
                "Workflow is not paused for HITL review."
            )

        action = str(action).upper()

        if action == "APPROVE":
            audit = self.reviewer_actions.approve(
                reviewer_id=reviewer_id,
                rationale=rationale,
                workflow_state="PAUSED",
            )

            return {
                "status": "APPROVED",
                "paused": False,
                "hitl_required": False,
                "audit": audit,
                "result": deepcopy(
                    paused_workflow.get(
                        "reasoning_critic"
                    )
                ),
            }

        if action == "REJECT":
            audit = self.reviewer_actions.reject(
                reviewer_id=reviewer_id,
                rationale=rationale,
                workflow_state="PAUSED",
            )

            return {
                "status": "REJECTED",
                "paused": False,
                "hitl_required": False,
                "audit": audit,
                "result": None,
            }

        if action == "EDIT":
            audit = self.reviewer_actions.edit(
                reviewer_id=reviewer_id,
                rationale=rationale,
                edited_result=edited_result,
                workflow_state="PAUSED",
            )

            return {
                "status": "EDITED",
                "paused": False,
                "hitl_required": False,
                "audit": audit,
                "result": deepcopy(
                    edited_result
                ),
            }

        return self._failure(
            f"Unsupported reviewer action: {action}"
        )

    def get_audit_log(self):
        return self.reviewer_actions.get_audit_log()

    def _failure(self, message):
        return {
            "status": "FAIL",
            "paused": False,
            "hitl_required": False,
            "audit": None,
            "result": None,
            "reason": message,
        }
