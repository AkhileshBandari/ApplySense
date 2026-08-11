import logging
from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Resume, ResumeAnalysis, ResumeVersion, TailoringChange
from jobs.models import Job
from .serializers import ResumeSerializer, ResumeAnalysisSerializer, ResumeVersionSerializer, TailoringChangeSerializer
from .services.extraction import extract_text, ExtractionError
from .services.parsing import ResumeParserService, ParsingError
from .services.provenance import ProvenanceService
from .services.analysis import ResumeAnalysisService
from .services.tailoring import ResumeTailoringService
from .services.rendering import ResumeRenderingService

from ai_engine.fallback_manager import AIFallbackManager
from ai_engine import prompts

import logging
logger = logging.getLogger(__name__)

class ResumeUploadView(views.APIView):
    """Handle resume file uploads, extract text, run AI parsing, and generate UNVERIFIED candidate facts."""

    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if "file" not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES["file"]
        file_name = file_obj.name

        resume = Resume.objects.create(
            user=request.user,
            file=file_obj,
            file_name=file_name,
            status='EXTRACTING'
        )
        file_path = resume.file.path

        # 1. Extraction
        try:
            text = extract_text(file_path, file_name)
            resume.parsed_text = text
            resume.status = 'PARSING'
            resume.save()
        except ExtractionError as e:
            resume.status = 'FAILED'
            resume.parsing_error = str(e)
            resume.save()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Parsing
        try:
            parser = ResumeParserService()
            parsed_data = parser.parse_resume(text)
            resume.parsed_data = parsed_data
            resume.status = 'REVIEW_REQUIRED'
            resume.save()
        except ParsingError as e:
            resume.status = 'FAILED'
            resume.parsing_error = str(e)
            resume.save()
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # 3. Provenance Import
        try:
            ProvenanceService.import_parsed_resume(request.user, resume, parsed_data)
        except Exception as e:
            logger.exception("Provenance import failed")
            return Response({"error": f"Failed to import facts: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = {
            "resume": ResumeSerializer(resume).data,
            "analysis": parsed_data,
        }
        return Response(payload, status=status.HTTP_201_CREATED)

class ResumeListView(generics.ListAPIView):
    """List all resumes belonging to the authenticated user."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ResumeSerializer

    def get_queryset(self):
        # We assume there's a created_at, but the model has uploaded_at.
        # Wait, the old code ordered by '-created_at', but the model has 'uploaded_at'. 
        # I'll fix it to '-uploaded_at'.
        return Resume.objects.filter(user=self.request.user).order_by("-uploaded_at")

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

class ResumeAnalyzeView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
        try:
            analysis = ResumeAnalysisService.analyze_general(resume)
            return Response(ResumeAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobSpecificAnalysisView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk, job_id):
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
        job = get_object_or_404(Job, pk=job_id)
        try:
            analysis = ResumeAnalysisService.analyze_job_specific(resume, job)
            return Response(ResumeAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeTailoringGenerateView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk, job_id=None):
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
        
        # If job_id is provided, use it. Otherwise, dynamically create a job.
        if job_id:
            job = get_object_or_404(Job, pk=job_id)
        else:
            job_desc = request.data.get('job_description')
            job_title = request.data.get('job_title', 'Unknown Title')
            job_company = request.data.get('job_company', 'Unknown Company')
            
            if not job_desc:
                return Response({"error": "job_description is required if job_id is not provided"}, status=status.HTTP_400_BAD_REQUEST)
                
            job = Job.objects.create(
                title=job_title,
                company=job_company,
                description=job_desc,
                portal_type='Manual'
            )

        try:
            version = ResumeTailoringService.generate_tailored_version(resume, job)
            return Response(ResumeVersionSerializer(version).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TailoringChangeReviewView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, change_id):
        # We need to ensure the user owns this change (via the version -> resume)
        change = get_object_or_404(TailoringChange, pk=change_id, version__user=request.user)
        
        user_decision = request.data.get('user_decision')
        proposed_text = request.data.get('proposed_text')

        if user_decision in dict(TailoringChange.USER_DECISIONS).keys():
            change.user_decision = user_decision
        
        if proposed_text is not None and proposed_text != change.proposed_text:
            # Re-validate user edit against CandidateContextService
            from profiles.services.candidate_context import CandidateContextService
            from resumes.services.claim_validation import ClaimValidationService
            import json

            context_service = CandidateContextService()
            verified_context = context_service.get_for_user(request.user)
            verified_context_json = json.dumps(verified_context, default=str)
            
            validation_status = ClaimValidationService.validate_claim(
                verified_evidence_text=verified_context_json,
                proposed_claim=proposed_text
            )

            if validation_status == "UNSUPPORTED":
                return Response(
                    {"error": "The proposed text contains unverified facts not found in your profile."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            change.proposed_text = proposed_text
            change.validation_status = validation_status
            change.user_decision = 'EDITED'

        change.save()
        return Response(TailoringChangeSerializer(change).data, status=status.HTTP_200_OK)


class ResumeVersionApproveView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, version_id):
        version = get_object_or_404(ResumeVersion, pk=version_id, user=request.user)
        try:
            version = ResumeTailoringService.approve_version(version)
            return Response(ResumeVersionSerializer(version).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResumeVersionDownloadView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, version_id):
        version = get_object_or_404(ResumeVersion, pk=version_id, user=request.user)
        try:
            file_stream = ResumeRenderingService.render_docx(version)
            response = HttpResponse(
                file_stream.read(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="tailored_resume_{version.id}.docx"'
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)