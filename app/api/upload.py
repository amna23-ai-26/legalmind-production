import os
import urllib.parse
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import get_upload_dir
from app.extraction.text_extractor import extract_text

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

# Allowed file types
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "jpg",
    "image/png": "png"
}

# Maximum file size = 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("")
async def upload_document(file: UploadFile = File(...)):

    # -----------------------------
    # 1. Check file type
    # -----------------------------
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, DOCX, JPG or PNG."
        )

    # -----------------------------
    # 2. Read file
    # -----------------------------
    contents = await file.read()

    # -----------------------------
    # 3. Check empty file
    # -----------------------------
    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    # -----------------------------
    # 4. Check file size
    # -----------------------------
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the 10 MB limit."
        )

    # -----------------------------
    # 5. Save file to dynamic dynamic config UPLOAD_DIR
    # -----------------------------
    file_type = ALLOWED_TYPES[file.content_type]
    
    # Decode URL-encoded characters (%20 -> spaces) and extract safe filename
    raw_filename = file.filename or "uploaded_file"
    clean_filename = urllib.parse.unquote(raw_filename)
    safe_filename = Path(clean_filename).name

    upload_dir = get_upload_dir()
    save_path = upload_dir / safe_filename

    try:
        with open(save_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file to disk: {str(e)}"
        )

    # -----------------------------
    # 6. Extract text
    # -----------------------------
    extracted_text = ""

    if file_type in ["pdf", "docx"]:
        try:
            extracted_text = extract_text(
                str(save_path),
                file_type
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Text extraction failed: {str(e)}"
            )

    # -----------------------------
    # 7. Return result
    # -----------------------------
    return {
        "filename": safe_filename,
        "content_type": file.content_type,
        "file_type": file_type,
        "size_bytes": len(contents),
        "text_characters": len(extracted_text),
        "text_words": len(extracted_text.split()),
        "text_preview": extracted_text[:1000],
        "status": "uploaded and processed successfully"
    }
