import json
from ai_engine.fallback_manager import AIFallbackManager
from ai_engine import prompts

class ParsingError(Exception):
    pass

class ResumeParserService:
    def __init__(self):
        self.ai = AIFallbackManager()

    def parse_resume(self, text: str) -> dict:
        """
        Uses AI to extract structured data from resume text.
        Validates basic structure to ensure valid JSON and expected keys.
        """
        system_prompt = prompts.RESUME_PARSE_SYSTEM_PROMPT
        user_prompt = prompts.RESUME_PARSE_USER_PROMPT.format(resume_text=text)

        try:
            ai_response = self.ai.generate_content(
                system_prompt,
                user_prompt,
                response_format_json=True,
            )
            parsed_data = self._clean_and_load_json(ai_response)
            self._validate_schema(parsed_data)
            return parsed_data
        except Exception as e:
            raise ParsingError(f"AI Parsing Error: {str(e)}")

    def _clean_and_load_json(self, response_text: str) -> dict:
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except Exception as e:
            raise ParsingError(f"Malformed JSON from AI provider: {str(e)}")
            
    def _validate_schema(self, data: dict):
        # Enforce basic expected keys for structural integrity
        expected_keys = [
            "contact", "summary", "skills", "experience", "education",
            "projects", "certifications", "achievements", "languages"
        ]
        
        if not isinstance(data, dict):
            raise ParsingError("Parsed data is not a dictionary.")
            
        for key in expected_keys:
            if key not in data:
                data[key] = [] if key not in ["contact", "summary"] else ({} if key == "contact" else "")
