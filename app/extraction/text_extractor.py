
import pymupdf
import pytesseract

from PIL import Image
from docx import Document


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a normal PDF.
    """

    text = []

    document = pymupdf.open(file_path)

    for page in document:
        page_text = page.get_text()
        text.append(page_text)

    document.close()

    return "\n".join(text).strip()


def extract_text_from_pdf_ocr(file_path: str) -> str:
    """
    Extract text from a scanned PDF using OCR.
    """

    text = []

    document = pymupdf.open(file_path)

    for page_number, page in enumerate(document):

        # Convert PDF page to image
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        # OCR
        page_text = pytesseract.image_to_string(image)

        text.append(page_text)

    document.close()

    return "\n".join(text).strip()


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file.
    """

    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(
                paragraph.text.strip()
            )

    return "\n".join(paragraphs).strip()


def extract_text(file_path: str, file_type: str) -> str:
    """
    Extract text based on document type.
    """

    if file_type == "pdf":

        text = extract_text_from_pdf(file_path)

        # If normal extraction returns enough text,
        # use it. Otherwise use OCR.
        if len(text.strip()) >= 100:
            return text

        return extract_text_from_pdf_ocr(file_path)


    elif file_type == "docx":

        return extract_text_from_docx(file_path)


    else:

        raise ValueError(
            "Unsupported file type. Only PDF and DOCX are supported."
        )
