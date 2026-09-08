
from app.agents import risk_agent
from app.agents.document_agent import DocumentAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.llm_risk_agent import LLMRiskAgent
from app.agents.reasoning.legal_reasoning_agent import LegalReasoningAgent
from app.agents.reasoning.llm_legal_reasoning_agent import LLMReasoningAgent
from app.agents.critic_agent import CriticAgent
from app.agents.explainability_agent import ExplainabilityAgent
from app.workflow.legalmind_state import LegalMindState
from langgraph.graph import StateGraph, START, END


class LegalMindGraph:
    def __init__(
        self,
        supervisor=None,
        planner=None,
        document_agent=None,
        llm_risk_agent=None,
        reasoning_agent=None,
        llm_reasoning_agent=None,
        critic_agent=None,
        explainability_agent=None,
        research_agent=None,
    ):
        self.planner = planner if planner is not None else PlannerAgent()
        self.supervisor = (
            supervisor
            if supervisor is not None
            else SupervisorAgent(planner=self.planner)
        )
        self.document_agent = (
            document_agent if document_agent is not None else DocumentAgent()
        )
        self.llm_risk_agent = llm_risk_agent
        self.reasoning_agent = reasoning_agent
        self.llm_reasoning_agent = llm_reasoning_agent
        self.critic_agent = critic_agent
        self.explainability_agent = explainability_agent
        self.research_agent = research_agent
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self):
        graph = StateGraph(LegalMindState)

        graph.add_node("initialize", self._initialize)
        graph.add_node("plan", self._plan)
        graph.add_node("document", self._document)
        graph.add_node("risk", self._risk)
        graph.add_node("research", self._research)
        graph.add_node("reasoning", self._reasoning)
        graph.add_node("critic", self._critic)
        graph.add_node("explainability", self._explainability)
        graph.add_node("complete", self._complete)

        graph.add_edge(START, "initialize")
        graph.add_edge("initialize", "plan")
        graph.add_edge("plan", "document")
        graph.add_edge("document", "risk")
        graph.add_edge("risk", "research")
        graph.add_edge("research", "reasoning")
        graph.add_edge("reasoning", "critic")
        graph.add_edge("critic", "explainability")
        graph.add_edge("explainability", "complete")
        graph.add_edge("complete", END)

        return graph

    def _initialize(self, state):
        return self.supervisor.initialize(
            document_id=state.get("document_id"),
            metadata=state.get("metadata", {}),
        )

    def _plan(self, state):
        plan = self.supervisor.plan(state)
        return {
            "plan": plan,
            "complexity": plan.get("complexity"),
            "execution_plan": plan.get("execution_plan", []),
        }

    def _document(self, state):
        file_path = state.get("file_path")
        file_type = state.get("file_type")

        if not file_path:
            return {
                "document_result": {
                    "status": "SKIPPED",
                    "reason": "file_path not provided",
                }
            }

        result = self.document_agent.process(
            file_path=file_path,
            file_type=file_type,
        )
        return {"document_result": result}

    def _risk(self, state):
        document_result = state.get("document_result") or {}
        clauses = document_result.get("clauses") or []

        findings = risk_agent.analyze_risks(clauses)

        if self.llm_risk_agent is not None:
            for clause in clauses:
                try:
                    llm_result = self.llm_risk_agent.analyze(clause)
                except Exception:
                    llm_result = None

                if isinstance(llm_result, dict):
                    findings.append(llm_result)

        return {"risk_findings": findings}

    def _research(self, state):
        document_result = state.get("document_result") or {}
        clauses = document_result.get("clauses") or []

        if self.research_agent is None or not clauses:
            return {
                "research_result": {
                    "status": "SKIPPED",
                    "reason": "research agent unavailable or no clauses",
                    "evidence": [],
                }
            }

        results = []

        for clause in clauses:
            try:
                result = self.research_agent.retrieve(
                    query=clause.get("text") or clause.get("heading") or "",
                    top_k=5,
                    retrieval_k=10,
                )
                results.append({
                    "clause": clause,
                    "result": result,
                })
            except Exception as exc:
                results.append({
                    "clause": clause,
                    "result": {
                        "status": "ERROR",
                        "error": str(exc),
                        "evidence": [],
                    },
                })

        return {
            "research_result": {
                "status": "COMPLETED",
                "results": results,
            }
        }

    def _reasoning(self, state):
        document_result = state.get("document_result") or {}
        clauses = document_result.get("clauses") or []
        risks = state.get("risk_findings") or []

        if not clauses:
            return {
                "reasoning_result": {
                    "status": "SKIPPED",
                    "reason": "no clauses available",
                }
            }

        clause = clauses[0]

        research_state = state.get("research_result") or {}
        research_items = research_state.get("results") or []

        research_result = {
            "clause": clause,
            "graph_authorities": [],
            "ranked_case_law": [],
            "evidence": [],
        }

        for item in research_items:
            item_clause = item.get("clause") or {}
            if item_clause.get("clause_id") == clause.get("clause_id"):
                result = item.get("result") or {}
                research_result.update({
                    "evidence": result.get("evidence") or [],
                    "corpus": result.get("corpus"),
                    "jurisdiction": result.get("jurisdiction"),
                })
                break

        result = None

        if self.llm_reasoning_agent is not None:
            try:
                result = self.llm_reasoning_agent.analyze(
                    research_result=research_result,
                    risk_findings=risks,
                )
            except Exception:
                result = None

        if result is None and self.reasoning_agent is not None:
            try:
                result = self.reasoning_agent.analyze_clause(
                    clause=clause,
                    risk_findings=risks,
                    legal_authorities=[],
                    case_law=[],
                    contract_id=state.get("document_id"),
                    clause_id=clause.get("clause_id"),
                )
            except Exception:
                result = None

        if result is not None and isinstance(result, dict):
            result = dict(result)
            evidence = research_result.get("evidence") or []
            result["evidence"] = evidence
            result["evidence_count"] = len(evidence)
            result["corpus"] = research_result.get("corpus")
            result["jurisdiction"] = research_result.get("jurisdiction")

        return {
            "reasoning_result": (
                result
                if result is not None
                else {
                    "status": "SKIPPED",
                    "reason": "reasoning agent unavailable",
                }
            )
        }

    def _critic(self, state):
        result = state.get("reasoning_result")

        if self.critic_agent is None or not isinstance(result, dict):
            return {
                "critic_result": {
                    "status": "SKIPPED",
                    "reason": "critic agent unavailable",
                }
            }

        try:
            research_state = state.get("research_result") or {}
            research_items = research_state.get("results") or []

            research_result = {
                "graph_authorities": [],
                "ranked_case_law": [],
                "evidence": [],
                "corpus": research_state.get("corpus"),
                "jurisdiction": research_state.get("jurisdiction"),
            }

            for item in research_items:
                item_result = item.get("result") or {}
                evidence = item_result.get("evidence") or []
                if evidence:
                    research_result["evidence"].extend(evidence)
                    research_result["corpus"] = (
                        research_result.get("corpus")
                        or item_result.get("corpus")
                    )
                    research_result["jurisdiction"] = (
                        research_result.get("jurisdiction")
                        or item_result.get("jurisdiction")
                    )

            critic_result = self.critic_agent.process(
                reasoning_result=result,
                research_result=research_result,
            )
        except Exception as exc:
            critic_result = {
                "status": "ERROR",
                "reason": str(exc),
            }

        return {"critic_result": critic_result}

    def _explainability(self, state):
        if self.explainability_agent is None:
            return {
                "explainability_result": {
                    "status": "SKIPPED",
                    "reason": "explainability agent unavailable",
                }
            }

        try:
            result = self.explainability_agent.process(
                reasoning_result=state.get("reasoning_result"),
                critic_result=state.get("critic_result"),
                research_result={
                    "graph_authorities": [],
                    "ranked_case_law": [],
                },
            )
        except Exception as exc:
            result = {
                "status": "ERROR",
                "reason": str(exc),
            }

        return {"explainability_result": result}

    def _complete(self, state):
        return self.supervisor.complete(
            state,
            status="COMPLETED",
        )

    def invoke(self, state):
        return self.app.invoke(state)
