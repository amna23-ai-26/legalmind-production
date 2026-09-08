from app.research.pakistan_evidence_adapter import PakistanEvidenceAdapter
from app.observability.phase4_langsmith import Phase4LangSmithInstrumentation
from app.security.phase4_security_boundary import Phase4SecurityExecutionBoundary
from app.workflow.phase3_workflow import Phase3Workflow


class PakistanPhase4Runtime:
    def __init__(
        self,
        hybrid_retriever,
        corpus_name,
        title,
        workflow,
        security_boundary=None,
        security_role="analyst",
        security_actor="phase4_runtime",
    ):
        self.evidence_adapter = PakistanEvidenceAdapter(
            hybrid_retriever=hybrid_retriever,
            corpus_name=corpus_name,
            title=title,
        )
        self.workflow = workflow
        self.instrumentation = Phase4LangSmithInstrumentation()
        self.security_boundary = security_boundary
        self.security_role = security_role
        self.security_actor = security_actor

    def process(
        self,
        contract_id,
        clause_id,
        clause,
        query,
        top_k=5,
        retrieval_k=10,
        risk_findings=None,
        reasoning_samples=None,
        evidence_graph=None,
    ):
        run_state = self.instrumentation.start_run(
            run_name="phase4_pakistan_runtime",
            metadata={
                "contract_id": contract_id,
                "clause_id": clause_id,
                "corpus": self.evidence_adapter.corpus_name,
            },
        )

        if self.security_boundary is not None:
            self.security_boundary.authorize(
                role=self.security_role,
                permission="read",
                actor=self.security_actor,
                event="phase4_runtime_process",
                metadata={
                    "contract_id": contract_id,
                    "clause_id": clause_id,
                    "corpus": self.evidence_adapter.corpus_name,
                },
            )

        research_result = self.evidence_adapter.build_research_result(
            contract_id=contract_id,
            clause_id=clause_id,
            clause=clause,
            query=query,
            top_k=top_k,
            retrieval_k=retrieval_k,
        )

        result = self.workflow.process(
            research_result=research_result,
            risk_findings=risk_findings,
            reasoning_samples=reasoning_samples,
            evidence_graph=evidence_graph,
        )

        observability = self.instrumentation.finish_run(
            run_state,
            status=result.get("status"),
            cycles_used=result.get("cycles_used"),
            retry_count=result.get("retry_count", 0),
            estimated_cost=result.get("estimated_cost", 0.0),
            override_action=result.get("override_action"),
        )

        result["phase4_observability"] = observability

        return result
