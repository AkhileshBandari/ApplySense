from ai_engine.fallback_manager import AIFallbackManager
import json

class InterviewRequirementAnalysisService:
    def __init__(self):
        self.ai = AIFallbackManager()

    def analyze_requirements(self, job_requirements):
        """
        Analyze normalized JobRequirements to extract required skills, 
        preferred skills, behavioral expectations, and technical stack.
        """
        if not job_requirements:
            return {}

        prompt = f"""
        Extract interview requirements from the following job requirements:
        {json.dumps(job_requirements)}
        
        Return a JSON with:
        - required_skills (list)
        - preferred_skills (list)
        - behavioral_expectations (list)
        - system_design_expectations (list)
        """
        
        try:
            response = self.ai.generate_content(
                "You are an expert technical interviewer.",
                prompt,
                response_format_json=True
            )
            return self._parse_json(response)
        except Exception:
            return {}
            
    def _parse_json(self, text):
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            return {}
