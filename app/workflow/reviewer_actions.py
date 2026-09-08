
from copy import deepcopy
from datetime import datetime, timezone


class ReviewerActions:
    """
    Phase 3 Reviewer Actions v1.

    Supports:
        APPROVE
        REJECT
        EDIT

    Every action creates an immutable audit record containing:
        reviewer_id
        timestamp
        rationale

    Existing audit records are never modified or deleted.
    """

    ALLOWED_ACTIONS = {
        "APPROVE",
        "REJECT",
        "EDIT",
    }

    def __init__(self):
        self._audit_log = []
        self._next_id = 1

    def approve(
        self,
        reviewer_id,
        rationale,
        workflow_state=None,
    ):
        return self._record(
            action="APPROVE",
            reviewer_id=reviewer_id,
            rationale=rationale,
            workflow_state=workflow_state,
        )

    def reject(
        self,
        reviewer_id,
        rationale,
        workflow_state=None,
    ):
        return self._record(
            action="REJECT",
            reviewer_id=reviewer_id,
            rationale=rationale,
            workflow_state=workflow_state,
        )

    def edit(
        self,
        reviewer_id,
        rationale,
        edited_result,
        workflow_state=None,
    ):
        return self._record(
            action="EDIT",
            reviewer_id=reviewer_id,
            rationale=rationale,
            edited_result=edited_result,
            workflow_state=workflow_state,
        )

    def get_audit_log(self):
        """
        Return a defensive copy of the audit log.

        Callers cannot modify the internal audit records.
        """
        return deepcopy(self._audit_log)

    def _record(
        self,
        action,
        reviewer_id,
        rationale,
        edited_result=None,
        workflow_state=None,
    ):
        if action not in self.ALLOWED_ACTIONS:
            raise ValueError(
                f"Unsupported reviewer action: {action}"
            )

        if not reviewer_id:
            raise ValueError(
                "reviewer_id is required"
            )

        if not rationale:
            raise ValueError(
                "rationale is required"
            )

        record = {
            "audit_id": self._next_id,
            "action": action,
            "reviewer_id": str(reviewer_id),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "rationale": str(rationale),
        }

        if workflow_state is not None:
            record["workflow_state"] = deepcopy(
                workflow_state
            )

        if action == "EDIT":
            record["edited_result"] = deepcopy(
                edited_result
            )

        self._audit_log.append(
            deepcopy(record)
        )

        self._next_id += 1

        return deepcopy(record)
