import logging
from rest_framework import views, status, permissions, generics, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from .models import Job, SavedJob, JobMatch
from .serializers import JobSerializer
from .services.ingestion import JobNormalizationService, JobValidationService
from .services.source_adapters import ManualCaptureAdapter
from .services.hybrid_matcher import HybridMatcherService

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobFeedView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Job.objects.filter(status='ACTIVE')
        
        # Filtering
        category = self.request.query_params.get('category')
        location = self.request.query_params.get('location')
        work_mode = self.request.query_params.get('work_mode')
        min_score = self.request.query_params.get('min_score')
        
        country = self.request.query_params.get('country')
        region = self.request.query_params.get('region')
        is_remote_worldwide = self.request.query_params.get('is_remote_worldwide')
        sponsorship_available = self.request.query_params.get('sponsorship_available')
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        if work_mode:
            queryset = queryset.filter(work_mode__iexact=work_mode)
            
        if country:
            queryset = queryset.filter(country__iexact=country)
        if region:
            queryset = queryset.filter(region__iexact=region)
        if is_remote_worldwide == 'true':
            queryset = queryset.filter(is_remote_worldwide=True)
        if sponsorship_available == 'true':
            queryset = queryset.filter(sponsorship_available=True)
            
        if category == 'SAVED':
            saved_job_ids = SavedJob.objects.filter(user=user).values_list('job_id', flat=True)
            queryset = queryset.filter(id__in=saved_job_ids)
            
        # We need to filter by score if requested. 
        # Since score is in JobMatch, we join it.
        if min_score:
            try:
                score = int(min_score)
                queryset = queryset.filter(matches__user=user, matches__overall_score__gte=score)
            except ValueError:
                pass
                
        from django.db.models import Prefetch
        
        # Order by recently discovered first if no score ordering
        return queryset.order_by("-discovered_at").select_related('requirements_norm').prefetch_related(
            Prefetch('matches', queryset=JobMatch.objects.filter(user=user)),
            Prefetch('savers', queryset=SavedJob.objects.filter(user=user))
        )


class JobDetailView(generics.RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticated,)


class ToggleSavedJobView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
            
        saved_job, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        
        if not created:
            saved_job.delete()
            return Response({"status": "unsaved"}, status=status.HTTP_200_OK)
            
        return Response({"status": "saved"}, status=status.HTTP_201_CREATED)


class JobCaptureView(views.APIView):
    """
    Accepts raw captured data from browser extension or manual input,
    normalizes it, creates a Job if valid, and runs the Hybrid Matcher.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        payload = request.data
        
        adapter = ManualCaptureAdapter()
        normalized_data = adapter.normalize(payload)
        
        if not JobValidationService.validate(normalized_data):
            return Response(
                {"error": "Invalid or incomplete job data."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Process creates or retrieves deduplicated job, and extracts requirements
            job = JobNormalizationService().process(normalized_data)
            
            # Match
            match = HybridMatcherService.match(request.user, job)
            
            serializer = JobSerializer(job, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Failed to process captured job")
            return Response(
                {"error": "Failed to process job: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )