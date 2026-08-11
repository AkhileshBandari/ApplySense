import json
from ai_engine.fallback_manager import AIFallbackManager

class IntentRouterService:
    INTENTS = [
        'GENERAL_CAREER',
        'JOB_COMPARISON',
        'JOB_FIT',
        'RESUME',
        'APPLICATION_ANALYSIS',
        'ANALYTICS',
        'SKILL_GAP',
        'LEARNING',
        'INTERVIEW_PREP',
        'PROFILE',
        'UNKNOWN'
    ]

    def __init__(self):
        self.ai = AIFallbackManager()

    def determine_intent(self, user_message: str, current_intent: str = None) -> str:
        """
        Classifies the user message into one of the supported intents.
        """
        system_prompt = (
            "You are an intent router for a Career Copilot AI. "
            "Your task is to classify the user's message into one of the following exact categories:\n"
            + ", ".join(self.INTENTS) + "\n\n"
            "Return ONLY a JSON object with a single key 'intent' containing the matched category.\n"
            "Example: {\"intent\": \"JOB_FIT\"}"
        )
        
        user_prompt = f"User Message:\n{user_message}"
        if current_intent:
            user_prompt += f"\n\nContext Note: The conversation was previously focused on {current_intent}."

        try:
            response = self.ai.generate_content(
                system_prompt,
                user_prompt,
                response_format_json=True
            )
            parsed = self._parse_json(response)
            intent = parsed.get("intent", "UNKNOWN")
            if intent not in self.INTENTS:
                intent = "UNKNOWN"
            return intent
        except Exception:
            return "UNKNOWN"

    def _parse_json(self, response_text: str) -> dict:
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except Exception:
            return {}
