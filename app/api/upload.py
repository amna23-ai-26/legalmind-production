
from fastapi import APIRouter, UploadFile, File, HTTPException
import os

from app.extraction.text_extractor import extract_text


router = APIRouter(
    prefix="/api",
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


# Folder where uploaded documents will be stored
UPLOAD_FOLDER = "/content/drive/MyDrive/legalmind/data/processed/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
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
    # 5. Save file
    # -----------------------------

    file_type = ALLOWED_TYPES[file.content_type]

    filename = file.filename or "uploaded_file"

    save_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    with open(save_path, "wb") as f:
        f.write(contents)


    # -----------------------------
    # 6. Extract text
    # -----------------------------

    extracted_text = ""

    if file_type in ["pdf", "docx"]:

        try:

            extracted_text = extract_text(
                save_path,
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
        "filename": filename,
        "content_type": file.content_type,
        "file_type": file_type,
        "size_bytes": len(contents),
        "text_characters": len(extracted_text),
        "text_words": len(extracted_text.split()),
        "text_preview": extracted_text[:1000],
        "status": "uploaded and processed successfully"
    }
