from typing import Any, Dict, List, Optional, TypedDict


class LegalMindState(TypedDict, total=False):
    document_id: str
    file_path: str
    file_type: str
    workflow_status: str
    metadata: Dict[str, Any]
    plan: Dict[str, Any]
    complexity: str
    execution_plan: List[str]
    document_result: Dict[str, Any]
    research_result: Dict[str, Any]
    risk_findings: List[Dict[str, Any]]
    reasoning_result: Dict[str, Any]
    critic_result: Dict[str, Any]
    explainability_result: Dict[str, Any]
    hitl_result: Dict[str, Any]
    report_result: Dict[str, Any]
    evidence_graph: Dict[str, Any]
    error: Optional[str]
    escalation_required: bool
    escalation_reason: Optional[str]
