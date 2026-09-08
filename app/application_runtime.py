from pathlib import Path
from uuid import uuid4

from app.agents.document_agent import DocumentAgent
from app.agents.risk_agent import analyze_risks
from app.report_generator import ReportGenerator


class LegalMindApplicationRuntime:
    VERSION = "application-runtime-v1"

    def __init__(self, phase4_runtime, report_output_dir):
        self.document_agent = DocumentAgent()
        self.phase4_runtime = phase4_runtime
        self.report_generator = ReportGenerator(report_output_dir)

    def process(self, file_path, file_type, corpus_name, corpus_title):
        file_path = str(Path(file_path))
        document_id = f"legalmind_{uuid4().hex[:12]}"

        document_result = self.document_agent.process(
            file_path=file_path,
            file_type=file_type,
        )

        clauses = document_result.get("clauses") or []
        risk_findings = analyze_risks(clauses)

        runtime_results = []

        for index, clause in enumerate(clauses, 1):
            clause_id = clause.get("clause_id") or index
            query = clause.get("text") or clause.get("heading") or ""

            if not query:
                continue

            result = self.phase4_runtime.process(
                contract_id=document_id,
                clause_id=clause_id,
                clause=clause,
                query=query,
                risk_findings=risk_findings,
            )

            runtime_results.append({
                "clause": clause,
                "result": result,
            })

        state = {
            "document_id": document_id,
            "file_path": file_path,
            "file_type": file_type,
            "workflow_status": "COMPLETED",
            "metadata": {
                "corpus": corpus_name,
                "jurisdiction": "Pakistan",
                "corpus_title": corpus_title,
            },
            "document_result": document_result,
            "risk_findings": risk_findings,
            "research_result": {
                "status": "COMPLETED",
                "results": runtime_results,
            },
        }

        report_result = self.report_generator.generate(state)

        state["report_result"] = report_result

        return state
