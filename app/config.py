import os
from pathlib import Path

# Base directory paths as Path objects
BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_data_dir() -> Path:
    """
    Resolve the directory that holds the processed legal corpus
    (data/phase4_pakistan/processed/...).

    An explicit DATA_DIR env var always wins. Otherwise this used to
    default unconditionally to <repo_root>/data — but the real,
    already-built corpus (chunks + embeddings for the Contract Act
    1872, Companies Act 2017, and Companies Regulations 2024) lives in
    this repo under <repo_root>/deployment/data instead. The Dockerfile
    only COPYs `app/` and `deployment/` into the image, never a
    top-level `data/`, so <repo_root>/data is always empty at runtime
    unless DATA_DIR is overridden. That silent mismatch is why
    /api/legal-query could never find any corpus and fell back to
    canned responses: build_retrievers() found no chunk files to load.

    Falling back to deployment/data when the plain data/ directory
    doesn't have the corpus fixes this for both the deployed container
    and local dev, without requiring a platform env var to be set.
    """
    env_value = os.getenv("DATA_DIR")
    if env_value:
        return Path(env_value)

    default_dir = BASE_DIR / "data"
    deployment_dir = BASE_DIR / "deployment" / "data"

    if not (default_dir / "phase4_pakistan").exists() and (deployment_dir / "phase4_pakistan").exists():
        return deployment_dir

    return default_dir


DATA_DIR = _resolve_data_dir()
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
