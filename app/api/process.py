
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.document_agent import DocumentAgent
from app.agents.risk_agent import analyze_risks

router = APIRouter(prefix="/api/process", tags=["Application Processing"])

UPLOAD_DIR = Path("/content/drive/MyDrive/legalmind/data/processed/uploads")

document_agent = DocumentAgent()


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
    risk_findings = analyze_risks(clauses)

    return {
        "status": "DOCUMENT_PROCESSED",
        "filename": file_path.name,
        "file_type": request.file_type,
        "document_result": document_result,
        "risk_findings": risk_findings,
        "clause_count": len(clauses),
    }
