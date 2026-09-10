import os
from pathlib import Path

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(DATA_DIR, "uploaded_pdfs"))
RUNTIME_RESULT_DIR = os.getenv("RUNTIME_RESULT_DIR", os.path.join(DATA_DIR, "runtime_results"))
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", os.path.join(DATA_DIR, "reports"))

# Ensure base directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RUNTIME_RESULT_DIR, exist_ok=True)
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)


def get_upload_dir():
    return UPLOAD_DIR


def get_data_dir():
    return DATA_DIR


def get_runtime_result_path(filename: str = ""):
    if filename:
        return os.path.join(RUNTIME_RESULT_DIR, filename)
    return RUNTIME_RESULT_DIR


def get_report_output_dir():
    return REPORT_OUTPUT_DIR
