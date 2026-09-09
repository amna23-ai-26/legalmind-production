from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.document_agent import DocumentAgent
from app.agents.risk_agent import analyze_risks
from app.production_runtime import build_production_runtime

router = APIRouter(prefix="/api/process", tags=["Application Processing"])

UPLOAD_DIR = Path("/content/drive/MyDrive/legalmind/data/processed/uploads")

document_agent = DocumentAgent()
phase4_runtime, workflow = build_production_runtime()


class ProcessRequest(BaseModel):
    filename: str
    file_type: str


@router.post("")
def process_document(request: ProcessRequest):
    file_path = UPLOAD_DIR / Path(request.filename).name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded document not found")

    document_result = document_agent.process(
        file_path=str(file_path),
        file_type=request.file_type,
    )

    clauses = document_result.get("clauses") or []

    if not clauses:
        raise HTTPException(
            status_code=422,
            detail="No clauses were extracted from the document",
        )

    risk_findings = analyze_risks(clauses)

    clause = clauses[0]

    if isinstance(clause, dict):
        clause_id = clause.get("clause_id") or clause.get("id") or 1
        clause_text = (
            clause.get("text")
            or clause.get("clause_text")
            or clause.get("content")
            or str(clause)
        )
    else:
        clause_id = 1
        clause_text = str(clause)

    workflow_result = phase4_runtime.process(
        contract_id=file_path.stem,
        clause_id=clause_id,
        clause=clause,
        query=clause_text,
        top_k=5,
        retrieval_k=10,
        risk_findings=risk_findings,
    )

    return {
        "status": workflow_result.get("status"),
        "filename": file_path.name,
        "file_type": request.file_type,
        "document_result": document_result,
        "risk_findings": risk_findings,
        "clause_count": len(clauses),
        "workflow_result": workflow_result,
    }
