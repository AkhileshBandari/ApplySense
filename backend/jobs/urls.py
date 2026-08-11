from django.urls import path
from .views import JobCaptureView, JobFeedView, JobDetailView, ToggleSavedJobView

urlpatterns = [
    path('capture/', JobCaptureView.as_view(), name='job_capture'),
    path('feed/', JobFeedView.as_view(), name='job_feed'),
    path('<int:pk>/', JobDetailView.as_view(), name='job_detail'),
    path('<int:pk>/save/', ToggleSavedJobView.as_view(), name='job_save_toggle'),
]
