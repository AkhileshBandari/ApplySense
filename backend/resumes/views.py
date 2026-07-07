import json
import logging
from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Resume
from .serializers import ResumeSerializer
from .parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    calculate_resume_health,
    calculate_ats_compatibility,
)

from ai_engine.fallback_manager import AIFallbackManager
from ai_engine import prompts

logger = logging.getLogger(__name__)


class ResumeUploadView(views.APIView):
    """Handle resume file uploads, extract text, compute health scores, and run AI parsing.

    The endpoint expects a multipart/form‑data request with a ``file`` field containing a PDF or DOCX.
    It saves the file, extracts the raw text, calculates health/ATS scores, then invokes the
    ``AIFallbackManager`` to generate a structured JSON analysis of the resume.
    """

    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # ------------------------------------------------------------------
        #   Validate upload
        # ------------------------------------------------------------------
        if "file" not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES["file"]
        file_name = file_obj.name

        # ------------------------------------------------------------------
        #   Persist the raw file so that it can be served later
        # ------------------------------------------------------------------
        resume = Resume.objects.create(
            user=request.user,
            file=file_obj,
            file_name=file_name,
        )

        file_path = resume.file.path

        # ------------------------------------------------------------------
        #   Extract raw text based on file type
        # ------------------------------------------------------------------
        text = ""
        if file_name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif file_name.lower().endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            # Fallback – try to read the uploaded bytes as UTF‑8 text
            try:
                text = file_obj.read().decode("utf-8", errors="ignore")
            except Exception as exc:  # pragma: no cover – extremely unlikely
                logger.exception("Failed to read raw upload %s", file_name)
                text = ""

        # ------------------------------------------------------------------
        #   Compute health & ATS compatibility scores (simple heuristics)
        # ------------------------------------------------------------------
        resume.parsed_text = text
        resume.health_score = calculate_resume_health(text)
        resume.ats_score = calculate_ats_compatibility(text)
        resume.save()

        # ------------------------------------------------------------------
        #   Run AI‑driven parsing – this may be a long operation, but we treat it
        #   synchronously for simplicity. In production you would push this to a
        #   background worker.
        # ------------------------------------------------------------------
        ai = AIFallbackManager()
        system_prompt = prompts.RESUME_PARSE_SYSTEM_PROMPT
        user_prompt = prompts.RESUME_PARSE_USER_PROMPT.format(resume_text=text)
        try:
            ai_raw = ai.generate_content(
                system_prompt, user_prompt, response_format_json=True
            )
            parsed = json.loads(ai_raw.strip())
        except Exception as exc:  # pragma: no cover – defensive fallback
            logger.exception("AI resume parsing failed")
            parsed = {"raw_output": ai_raw if "ai_raw" in locals() else ""}

        # ------------------------------------------------------------------
        #   Return a combined payload – the original serializer plus the AI
        #   analysis. Clients can decide what they need.
        # ------------------------------------------------------------------
        payload = {
            "resume": ResumeSerializer(resume).data,
            "analysis": parsed,
        }
        return Response(payload, status=status.HTTP_201_CREATED)


class ResumeListView(generics.ListAPIView):
    """List all resumes belonging to the authenticated user."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ResumeSerializer

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by("-created_at")

class ResumeDetailView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk):
        resume = get_object_or_404(
            Resume,
            pk=pk,
            user=request.user
        )

        return Response(
            ResumeSerializer(resume).data,
            status=status.HTTP_200_OK
        )

class ResumeTailorView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        resume_id = request.data.get("resume_id")
        job_description = request.data.get("job_description")

        if not resume_id or not job_description:
            return Response(
                {
                    "error": "resume_id and job_description are required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume = get_object_or_404(
            Resume,
            pk=resume_id,
            user=request.user,
        )

        ai = AIFallbackManager()

        try:
            result = ai.generate_content(
                prompts.RESUME_TAILOR_SYSTEM_PROMPT,
                f"""
Resume:
{resume.parsed_text}

Job Description:
{job_description}
""",
                response_format_json=True,
            )

            return Response(
                {"tailored_resume": result},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )