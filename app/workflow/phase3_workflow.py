
from app.workflow.hitl_trigger import HITLTrigger
from app.workflow.reasoning_critic_loop import ReasoningCriticLoop
from app.agents.explainability_agent import ExplainabilityAgent


class Phase3Workflow:
    """
    Phase 3 workflow coordinator.

    Routes risk findings through HITL before the existing
    Reasoning <-> Critic loop.

    Existing validated components are used unchanged.
    """

    def __init__(
        self,
        reasoning_critic_loop,
        explainability_agent=None,
        hitl_trigger=None,
    ):
        self.reasoning_critic_loop = reasoning_critic_loop
        self.explainability_agent = (
            explainability_agent
            if explainability_agent is not None
            else ExplainabilityAgent()
        )
        self.hitl_trigger = (
            hitl_trigger
            if hitl_trigger is not None
            else HITLTrigger()
        )

    def process(
        self,
        research_result,
        risk_findings=None,
        reasoning_samples=None,
        evidence_graph=None,
    ):
        hitl_result = self.hitl_trigger.evaluate(
            risk_findings or []
        )

        if hitl_result.get("hitl_required") is True:
            return {
                "status": "PAUSED",
                "paused": True,
                "hitl_required": True,
                "hitl": hitl_result,
                "reasoning_critic": None,
                "explainability": None,
            }

        reasoning_critic_result = (
            self.reasoning_critic_loop.process(
                research_result,
                risk_findings=risk_findings,
            )
        )

        if not reasoning_critic_result.get("passed"):
            return {
                "status": reasoning_critic_result.get(
                    "status",
                    "SUPERVISOR_ESCALATION",
                ),
                "paused": False,
                "hitl_required": False,
                "hitl": hitl_result,
                "reasoning_critic": reasoning_critic_result,
                "explainability": None,
            }

        explainability_result = (
            self.explainability_agent.process(
                reasoning_result=(
                    reasoning_critic_result[
                        "reasoning_result"
                    ]
                ),
                research_result=research_result,
                critic_result=(
                    reasoning_critic_result[
                        "critic_result"
                    ]
                ),
                reasoning_samples=reasoning_samples,
                evidence_graph=evidence_graph,
            )
        )

        return {
            "status": "PASS",
            "paused": False,
            "hitl_required": False,
            "hitl": hitl_result,
            "reasoning_critic": reasoning_critic_result,
            "explainability": explainability_result,
        }
