class ReasoningCriticLoop:
    """
    Phase 3 Reasoning <-> Critic revision loop.

    Orchestrates:
        LegalReasoningAgent
        CriticAgent

    Critic remains closed-world and only evaluates
    ResearchAgent evidence.

    Maximum revision cycles: 3.
    """

    def __init__(
        self,
        reasoning_agent,
        critic_agent,
        max_cycles=3,
        revision_handler=None,
    ):
        self.reasoning_agent = reasoning_agent
        self.critic_agent = critic_agent
        self.max_cycles = max_cycles
        self.revision_handler = revision_handler

        if self.max_cycles != 3:
            raise ValueError(
                "Phase 3 revision loop must be capped at 3 cycles."
            )

    def process(
        self,
        research_result,
        risk_findings=None,
    ):
        if not isinstance(research_result, dict):
            return self._failure(
                "research_result must be a dictionary"
            )

        history = []
        reasoning_result = None
        critic_result = None
        revision_instructions = []

        for cycle in range(1, self.max_cycles + 1):

            if cycle == 1 or self.revision_handler is None:
                reasoning_result = self.reasoning_agent.process(
                    research_result,
                    risk_findings=risk_findings,
                )
            else:
                reasoning_result = self.revision_handler(
                    reasoning_result=reasoning_result,
                    research_result=research_result,
                    risk_findings=risk_findings,
                    revision_instructions=revision_instructions,
                    cycle=cycle,
                )

            critic_result = self.critic_agent.process(
                reasoning_result,
                research_result,
            )

            revision_instructions = critic_result.get(
                "revision_instructions",
                [],
            )

            cycle_record = {
                "cycle": cycle,
                "reasoning_result": reasoning_result,
                "critic_result": critic_result,
                "critic_status": critic_result.get(
                    "status"
                ),
                "passed": bool(
                    critic_result.get("passed")
                ),
                "revision_instructions": revision_instructions,
            }

            history.append(cycle_record)

            if critic_result.get("passed") is True:
                return {
                    "status": "PASS",
                    "passed": True,
                    "cycles_used": cycle,
                    "max_cycles": self.max_cycles,
                    "reasoning_result": reasoning_result,
                    "critic_result": critic_result,
                    "history": history,
                    "supervisor_escalation": {
                        "required": False,
                        "reason": None,
                    },
                }

        return {
            "status": "SUPERVISOR_ESCALATION",
            "passed": False,
            "cycles_used": self.max_cycles,
            "max_cycles": self.max_cycles,
            "reasoning_result": reasoning_result,
            "critic_result": critic_result,
            "history": history,
            "supervisor_escalation": {
                "required": True,
                "reason": (
                    "Critic review failed after the maximum "
                    "of 3 revision cycles."
                ),
            },
        }

    def _failure(self, message):
        return {
            "status": "FAIL",
            "passed": False,
            "cycles_used": 0,
            "max_cycles": self.max_cycles,
            "reasoning_result": None,
            "critic_result": None,
            "history": [],
            "supervisor_escalation": {
                "required": False,
                "reason": message,
            },
        }
