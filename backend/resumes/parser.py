import re
from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_path) -> str:
    """Extract raw text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"PDF Extraction Error: {str(e)}"


def extract_text_from_docx(file_path) -> str:
    """Extract raw text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception as e:
        return f"DOCX Extraction Error: {str(e)}"


def calculate_resume_health(text: str) -> int:
    """
    Evaluates resume quality based on presence of key contact details,
    length, and standard headings. Returns a score between 0 and 100.
    """
    if not text:
        return 0

    score = 40  # Base score for having any text

    # 1️⃣ Contact info
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):  # Email
        score += 10
    if re.search(r'\+?\d[\d\s\(\)-]{7,15}', text):  # Phone
        score += 10
    if re.search(r'linkedin\.com/in/\w+', text, re.IGNORECASE):
        score += 10
    if re.search(r'github\.com/\w+', text, re.IGNORECASE):
        score += 5

    # 2️⃣ Key sections
    sections = ['experience', 'education', 'skills', 'projects', 'summary']
    for sec in sections:
        if re.search(rf'\b{sec}\b', text, re.IGNORECASE):
            score += 4

    # 3️⃣ Word count (ideal 300‑1200)
    words = len(text.split())
    if 300 <= words <= 1200:
        score += 5
    elif words > 1200:
        score += 2  # Too long, slight penalty

    return min(score, 100)


def calculate_ats_compatibility(text: str) -> int:
    """
    Rough ATS‑compatibility scoring.
    Checks for:
      • Simple formatting (no tables, minimal special characters)
      • Presence of common section headings
      • Use of standard fonts/keywords
    Returns a score 0‑100.
    """
    score = 30  # Start with a low baseline

    # Simple formatting – penalise excessive HTML tags or markdown
    if re.search(r'<[^>]+>', text):
        score -= 10
    if re.search(r'```', text):
        score -= 5

    # Section headings
    headings = ['summary', 'experience', 'education', 'skills', 'projects', 'certifications']
    found = sum(1 for h in headings if re.search(rf'\b{h}\b', text, re.IGNORECASE))
    score += found * 5

    # Keyword density – presence of common tech terms
    tech_terms = [
        "python", "django", "react", "javascript", "java", "c#", "c++",
        "aws", "docker", "kubernetes", "sql", "git", "rest", "graphql",
    ]
    term_hits = sum(1 for t in tech_terms if re.search(rf'\b{t}\b', text, re.IGNORECASE))
    score += min(term_hits * 2, 20)  # cap at +20

    # Length sanity
    words = len(text.split())
    if 300 <= words <= 1500:
        score += 10
    elif words < 300:
        score -= 5
    else:
        score -= 5

    return max(0, min(100, score))
