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
        except Exception:
            return {"raw_output": response_text}


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

        ai_response = self.ai.generate_content(
            system_prompt,
            user_prompt,
            response_format_json=True,
        )
        parsed = self.parse_ai_json(ai_response)
        return Response(parsed, status=status.HTTP_200_OK)
# ----------------------------------------------------------------------
# Skill Gap Analysis
# ----------------------------------------------------------------------
class SkillGapAnalysisView(BaseCoachView):
    def post(self, request):
        resume_text = request.data.get("resume_text", "")
        target_role = request.data.get("target_role", "")

        if not resume_text or not target_role:
            return Response(
                {
                    "error": "resume_text and target_role are required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_response = self.ai.generate_content(
            prompts.COACH_SKILL_GAP_SYSTEM_PROMPT,
            f"""
Resume:
{resume_text}

Target Role:
{target_role}
""",
            response_format_json=True,
        )

        return Response(
            self.parse_ai_json(ai_response),
            status=status.HTTP_200_OK,
        )



class LearningRoadmapView(BaseCoachView):
    def post(self, request):
        missing_skills = request.data.get("missing_skills", [])

        if not missing_skills:
            return Response(
                {
                    "error": "missing_skills is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_response = self.ai.generate_content(
            prompts.COACH_ROADMAP_SYSTEM_PROMPT,
            f"Missing Skills: {missing_skills}",
            response_format_json=True,
        )

        return Response(
            self.parse_ai_json(ai_response),
            status=status.HTTP_200_OK,
        )



    def post(self, request):
        role = request.data.get("role", "")
        experience = request.data.get("experience", "")

        if not role:
            return Response(
                {
                    "error": "role is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_response = self.ai.generate_content(
            prompts.INTERVIEW_PREP_SYSTEM_PROMPT,
            f"""
Role: {role}
Experience: {experience}
""",
            response_format_json=True,
        )

        return Response(
            self.parse_ai_json(ai_response),
            status=status.HTTP_200_OK,
        )

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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
