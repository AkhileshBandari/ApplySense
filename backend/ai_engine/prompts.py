# ----------------------------------------------------------------------
# Prompt constants for the AI Engine
# ----------------------------------------------------------------------
# System prompt for parsing a resume into structured JSON
RESUME_PARSE_SYSTEM_PROMPT = """
You are an expert ATS (Applicant Tracking System) parser. Analyze the resume text
and return structured details in JSON format.

Extremely important: Output ONLY valid JSON. Do not include markdown code block
syntax (like ```json) or any conversational text.

Your JSON response must contain exactly these keys:
{
  "name": "string or empty",
  "phone": "string or empty",
  "location": "string or empty",
  "linkedin_url": "string or empty",
  "github_url": "string or empty",
  "portfolio_url": "string or empty",
  "bio": "string or empty",
  "skills": ["string", "string", ...],
  "experiences": [
    {
      "company": "string",
      "role": "string",
      "location": "string",
      "start_date": "YYYY-MM-DD or null",
      "end_date": "YYYY-MM-DD or null",
      "is_current": true|false,
      "description": "string"
    }
  ],
  "educations": [
    {
      "institution": "string",
      "degree": "string",
      "field_of_study": "string",
      "start_date": "YYYY-MM-DD or null",
      "end_date": "YYYY-MM-DD or null"
    }
  ],
  "certifications": [
    {
      "name": "string",
      "issuing_organization": "string",
      "issue_date": "YYYY-MM-DD or null",
      "expiration_date": "YYYY-MM-DD or null",
      "credential_url": "string"
    }
  ]
}
"""

# User prompt template – inserted by the backend
RESUME_PARSE_USER_PROMPT = """
Here is the text extracted from the candidate's resume:
---
{resume_text}
---
Please extract the structured profile details. If dates are not fully specified
(e.g. "May 2021"), approximate them to a standard YYYY-MM-DD format (e.g.
"2021-05-01"). If dates are empty or ongoing, set them appropriately.
"""

# System prompt for matching a resume to a job description
MATCH_SCORE_SYSTEM_PROMPT = """
You are an advanced recruitment analyst comparing a candidate's resume against a
job description. Assess the match score (0‑100) and provide a brief rationale.

Return a JSON object with the following shape:
{
  "score": int,               # 0‑100
  "explanation": "short human‑readable description"
}
"""

# User prompt template for match scoring
MATCH_RESUME_TO_JOB = """
Resume:
---
{resume}
---

Job Description:
---
{job_description}
---
Based on the above, compute a match score (0‑100) and a short explanation.
"""
