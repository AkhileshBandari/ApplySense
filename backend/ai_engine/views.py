import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .fallback_manager import AIFallbackManager
from . import prompts


class BaseCoachView(APIView):
    """
    Base view that initialises the AI fallback manager and provides a helper
    for cleaning up LLM JSON responses.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai = AIFallbackManager()

    @staticmethod
    def parse_ai_json(response_text: str):
        """
        Strip markdown code fences and parse JSON. Returns the parsed dict or
        a fallback dict containing the raw output.
        """
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except Exception as e:
            raise ValueError("AI provider returned malformed JSON") from e


# ----------------------------------------------------------------------
# Resume parsing endpoint
# ----------------------------------------------------------------------
class ResumeParseView(BaseCoachView):
    def post(self, request):
        resume_text = request.data.get('resume_text', '')
        if not resume_text:
            return Response(
                {"error": "resume_text field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        system_prompt = prompts.RESUME_PARSE_SYSTEM_PROMPT
        user_prompt = prompts.RESUME_PARSE_USER_PROMPT.format(resume_text=resume_text)

        try:
            ai_response = self.ai.generate_content(
                system_prompt,
                user_prompt,
                response_format_json=True,
            )
            parsed = self.parse_ai_json(ai_response)
            return Response(parsed, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
# ----------------------------------------------------------------------
# Skill Gap Analysis
# ----------------------------------------------------------------------


class InterviewPrepView(BaseCoachView):
    def post(self, request):
        role = request.data.get("role", "")
        experience = request.data.get("experience", "")

        if not role:
            return Response(
                {"error": "role is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ai_response = self.ai.generate_content(
                "You are an expert interview coach.",
                f"""
Role: {role}
Experience: {experience}
Generate interview preparation guidance.
""",
                response_format_json=True,
            )

            return Response(
                self.parse_ai_json(ai_response),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
