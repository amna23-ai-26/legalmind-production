import os
from pathlib import Path

# Base directory paths as Path objects
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", DATA_DIR / "uploaded_pdfs"))
RUNTIME_RESULT_DIR = Path(os.getenv("RUNTIME_RESULT_DIR", DATA_DIR / "runtime_results"))
REPORT_OUTPUT_DIR = Path(os.getenv("REPORT_OUTPUT_DIR", DATA_DIR / "reports"))

# Ensure base directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RUNTIME_RESULT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_upload_dir() -> Path:
    return UPLOAD_DIR


def get_data_dir() -> Path:
    return DATA_DIR


def get_runtime_result_path(filename: str = "") -> Path:
    if filename:
        return RUNTIME_RESULT_DIR / filename
    return RUNTIME_RESULT_DIR


def get_report_output_dir() -> Path:
    return REPORT_OUTPUT_DIR
