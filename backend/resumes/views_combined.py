import json
import logging
from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

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


# ----------------------------------------------------------------------
#   Application‑related views (analytics & basic CRUD)
# ----------------------------------------------------------------------

from rest_framework import viewsets
from django.db.models import Avg, Count
from collections import Counter

from .models import Application, Interview, ApplicationNote
from .serializers import (
    ApplicationSerializer,
    InterviewSerializer,
    ApplicationNoteSerializer,
)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).order_by("-updated_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InterviewViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Interview.objects.filter(application__user=self.request.user).order_by("scheduled_at")

    def perform_create(self, serializer):
        app_id = self.request.data.get("application")
        application = Application.objects.get(pk=app_id, user=self.request.user)
        serializer.save(application=application)


class ApplicationNoteViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationNoteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ApplicationNote.objects.filter(application__user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        app_id = self.request.data.get("application")
        application = Application.objects.get(pk=app_id, user=self.request.user)
        serializer.save(application=application)


class AnalyticsView(views.APIView):
    """Return high‑level statistics for the current user's job applications.

    The response shape mirrors what the front‑end expects for the dashboard:
    ``total``, ``status_breakdown`` (a mapping of status → count), and ``average_match_score``.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user_apps = Application.objects.filter(user=request.user)
        total_apps = user_apps.count()

        # Status breakdown – ``status`` is assumed to be a CharField on Application
        status_qs = user_apps.values("status").annotate(cnt=Count("status"))
        status_breakdown = {item["status"]: item["cnt"] for item in status_qs}

        avg_match = user_apps.aggregate(avg=Avg("match_score"))["avg"] or 0

        data = {
            "total_applications": total_apps,
            "status_breakdown": status_breakdown,
            "average_match_score": round(avg_match, 2),
        }
        return Response(data, status=status.HTTP_200_OK)
