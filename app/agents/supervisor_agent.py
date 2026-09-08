class SupervisorAgent:
    """
    LegalMind top-level workflow supervisor.

    Coordinates planning, execution status, escalation,
    and completion state without modifying frozen agents.
    """

    def __init__(self, planner=None):
        self.planner = planner

    def initialize(self, document_id, metadata=None):
        return {
            "document_id": str(document_id),
            "workflow_status": "INITIALIZED",
            "escalation_required": False,
            "escalation_reason": None,
            "metadata": metadata or {},
        }

    def plan(self, state):
        if not isinstance(state, dict):
            raise ValueError("state must be a dictionary")

        if self.planner is None:
            raise ValueError("planner is required")

        return self.planner.create_plan(
            document_id=state.get("document_id"),
            metadata=state.get("metadata", {}),
        )

    def complete(self, state, status="COMPLETED"):
        result = dict(state)
        result["workflow_status"] = status
        return result

    def escalate(self, state, reason):
        result = dict(state)
        result["workflow_status"] = "ESCALATED"
        result["escalation_required"] = True
        result["escalation_reason"] = str(reason)
        return result
