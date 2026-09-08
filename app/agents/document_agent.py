
import os

from app.extraction.text_extractor import extract_text
from app.extraction.clause_segmenter import segment_clauses


class DocumentAgent:
    """
    LegalMind Phase 1 Document Agent.

    Responsible for:
    - validating uploaded documents
    - extracting document text
    - segmenting the document into clauses
    - returning a structured document representation

    Existing Phase 1 extraction components are reused directly.
    """

    ALLOWED_TYPES = {
        "pdf",
        "docx",
        "jpg",
        "jpeg",
        "png"
    }

    def __init__(self):
        pass

    def process(
        self,
        file_path,
        file_type
    ):
        """
        Process one legal document.

        Parameters
        ----------
        file_path : str
            Path to the document.

        file_type : str
            pdf, docx, jpg, jpeg, or png.

        Returns
        -------
        dict
            Structured document-analysis result.
        """

        # --------------------------------------------------
        # 1. Validate file
        # --------------------------------------------------

        if not file_path:
            raise ValueError(
                "file_path is required."
            )

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        file_type = str(
            file_type
        ).lower().lstrip(".")

        if file_type not in self.ALLOWED_TYPES:
            raise ValueError(
                f"Unsupported file type: {file_type}"
            )

        # --------------------------------------------------
        # 2. Extract text
        # --------------------------------------------------

        text = extract_text(
            file_path,
            file_type
        )

        if not text or not text.strip():
            raise ValueError(
                "No text could be extracted from the document."
            )

        # --------------------------------------------------
        # 3. Segment clauses
        # --------------------------------------------------

        clauses = segment_clauses(
            text
        )

        # --------------------------------------------------
        # 4. Normalize clause output
        # --------------------------------------------------

        normalized_clauses = []

        for index, clause in enumerate(
            clauses,
            start=1
        ):

            if isinstance(clause, dict):

                item = dict(clause)

                item.setdefault(
                    "clause_id",
                    index
                )

                item.setdefault(
                    "text",
                    ""
                )

                item.setdefault(
                    "heading",
                    ""
                )

            else:

                item = {
                    "clause_id": index,
                    "heading": "",
                    "text": str(clause)
                }

            normalized_clauses.append(
                item
            )

        # --------------------------------------------------
        # 5. Return structured result
        # --------------------------------------------------

        return {
            "filename": os.path.basename(
                file_path
            ),
            "file_path": file_path,
            "file_type": file_type,
            "text": text,
            "text_characters": len(text),
            "text_words": len(text.split()),
            "clause_count": len(
                normalized_clauses
            ),
            "clauses": normalized_clauses,
            "status": "processed"
        }
