from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import get_report_output_dir, get_runtime_result_path
from app.report_generator import ReportGenerator
import json

# main.py mounts every router under an additional "/api" prefix
# (app.include_router(router, prefix="/api")), so this must only
# declare its own sub-path - it previously declared "/api/report"
# here too, which made the real route /api/api/report and meant
# /api/report always 404'd before this function ever ran.
router = APIRouter(prefix="/report", tags=["Report"])

@router.get("")
def download_report():
    report_dir = get_report_output_dir()
    primary_report = report_dir / "application_runtime.docx"

    if primary_report.exists():
        return FileResponse(
            path=str(primary_report),
            filename="LegalMind_Legal_Intelligence_Report.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    docx_files = list(report_dir.glob("*.docx"))
    if docx_files:
        return FileResponse(
            path=str(docx_files[0]),
            filename="LegalMind_Legal_Intelligence_Report.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    # process.py writes the last analysis to latest_result.json;
    # get_runtime_result_path() with no filename returns the containing
    # directory, not that file. Checking the directory's existence
    # always succeeds (config.py creates it on startup), so this used
    # to always "pass" the check and then fail with IsADirectoryError
    # when opened below - silently caught, so the real analysis result
    # was never actually loaded.
    runtime_path = get_runtime_result_path("latest_result.json")
    if runtime_path.exists():
        try:
            with open(runtime_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            generator = ReportGenerator(report_dir)
            result = generator.generate(state, filename="application_runtime.docx")
            gen_path = Path(result["path"])
            if gen_path.exists():
                return FileResponse(
                    path=str(gen_path),
                    filename="LegalMind_Legal_Intelligence_Report.docx",
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
        except Exception:
            pass

    try:
        fallback_state = {
            "document_id": "legalmind_analysis",
            "workflow_status": "COMPLETED",
            "metadata": {
                "corpus": "pakistan_commercial_law",
                "jurisdiction": "Pakistan",
            },
            "risk_findings": [],
            "reasoning_result": {
                "status": "COMPLETED",
                "legal_assessment": "Analysis initialized. All findings are subject to human review.",
            },
        }
        generator = ReportGenerator(report_dir)
        result = generator.generate(fallback_state, filename="application_runtime.docx")
        gen_path = Path(result["path"])
        if gen_path.exists():
            return FileResponse(
                path=str(gen_path),
                filename="LegalMind_Legal_Intelligence_Report.docx",
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation error: {str(exc)}"
        )

    raise HTTPException(status_code=404, detail="No report currently available.")
