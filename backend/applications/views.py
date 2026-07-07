from rest_framework import viewsets, permissions, views, status
from rest_framework.response import Response
from django.db.models import Avg, Count

from .models import Application, Interview, ApplicationNote
from .serializers import ApplicationSerializer, InterviewSerializer, ApplicationNoteSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    """CRUD for user applications."""
    serializer_class = ApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InterviewViewSet(viewsets.ModelViewSet):
    """CRUD for interviews linked to an application."""
    serializer_class = InterviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Interview.objects.filter(application__user=self.request.user).order_by('scheduled_at')

    def perform_create(self, serializer):
        app_id = self.request.data.get('application')
        application = Application.objects.get(pk=app_id, user=self.request.user)
        serializer.save(application=application)


class ApplicationNoteViewSet(viewsets.ModelViewSet):
    """CRUD for notes attached to applications."""
    serializer_class = ApplicationNoteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ApplicationNote.objects.filter(application__user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        app_id = self.request.data.get('application')
        application = Application.objects.get(pk=app_id, user=self.request.user)
        serializer.save(application=application)


class AnalyticsView(views.APIView):
    """Provide high‑level stats for the dashboard.

    Returns total number of applications, a breakdown by status, and the average match score.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user_apps = Application.objects.filter(user=request.user)
        total_apps = user_apps.count()

        # Status breakdown (e.g., Saved, Applied, Interview, Offer, Rejected)
        status_qs = user_apps.values('status').annotate(cnt=Count('status'))
        status_breakdown = {item['status']: item['cnt'] for item in status_qs}

        avg_match = user_apps.aggregate(avg=Avg('match_score'))['avg'] or 0

        data = {
            'total_applications': total_apps,
            'status_breakdown': status_breakdown,
            'average_match_score': round(avg_match, 2),
        }
        return Response(data, status=status.HTTP_200_OK)
