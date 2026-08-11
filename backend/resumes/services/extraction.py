import re
from pypdf import PdfReader
from docx import Document

class ExtractionError(Exception):
    pass

def extract_text(file_path, file_name) -> str:
    """Extract raw text from a PDF or DOCX file."""
    if file_name.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_name.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        raise ExtractionError(f"Unsupported file format: {file_name}")

def extract_text_from_pdf(file_path) -> str:
    """Extract raw text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ExtractionError("PDF Extraction Error: No extractable text found")
        return cleaned_text
    except ExtractionError as e:
        raise e
    except Exception as e:
        raise ExtractionError(f"PDF Extraction Error: {str(e)}")


def extract_text_from_docx(file_path) -> str:
    """Extract raw text from a DOCX file."""
    try:
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs).strip()
        if not text:
            raise ExtractionError("DOCX Extraction Error: No extractable text found")
        return text
    except ExtractionError as e:
        raise e
    except Exception as e:
        raise ExtractionError(f"DOCX Extraction Error: {str(e)}")
