import json

from ai_engine.fallback_manager import AIFallbackManager
from ai_engine import prompts


class AIEvaluationEngine:
    """A lightweight evaluation engine inspired by Career-Ops scoring logic."""

    def evaluate_job(self, job: dict | None = None, resume_text: str | None = None, profile: object | None = None) -> dict:
        job = job or {}
        resume_text = resume_text or ""

        ai = AIFallbackManager()
        response = ai.generate_content(
            prompts.MATCH_SCORE_SYSTEM_PROMPT,
            f"Resume:\n{resume_text}\n\nJob Description:\n{job.get('description', '')}",
            response_format_json=True,
        )
        parsed = self._parse_json(response)
        
        score = 0
        summary = ""
        matched_keywords = []

        if isinstance(parsed, dict):
            score = int(parsed.get("score", 0))
            summary = parsed.get("explanation", "")
            # we can infer matched keywords if the AI returns them, otherwise empty
            matched_keywords = parsed.get("matched_keywords", [])

        return {
            "score": max(0, min(100, score)),
            "grade": self._grade(score),
            "summary": summary,
            "matched_keywords": matched_keywords,
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
            return {"score": 0, "explanation": response_text}

    @staticmethod
    def _grade(score: int) -> str:
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 55:
            return "C"
        if score >= 40:
            return "D"
        return "F"
