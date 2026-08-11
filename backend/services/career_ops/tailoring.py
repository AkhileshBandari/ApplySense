import json

from ai_engine.fallback_manager import AIFallbackManager
from ai_engine import prompts


class ResumeTailoringEngine:
    """Create a simple tailored resume summary and highlights from a job description."""

    def tailor_resume(self, resume_text: str | None = None, job_description: str | None = None) -> dict:
        resume_text = resume_text or ""
        job_description = job_description or ""

        ai = AIFallbackManager()
        response = ai.generate_content(
            prompts.RESUME_TAILOR_SYSTEM_PROMPT,
            f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}",
            response_format_json=True,
        )
        parsed = self._parse_json(response)
        
        summary = ""
        highlights = []
        keywords = []

        if isinstance(parsed, dict):
            summary = parsed.get("tailored_summary", "")
            highlights = parsed.get("highlights", [])
            keywords = parsed.get("keywords", [])

        return {
            "tailored_summary": summary,
            "highlights": highlights,
            "keywords": keywords,
        }

    @staticmethod
    def _parse_json(response_text: str) -> dict:
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1)
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"tailored_summary": response_text, "highlights": [], "keywords": []}
