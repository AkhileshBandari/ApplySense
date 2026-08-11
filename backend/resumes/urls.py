from django.urls import path
from .views import (
    ResumeUploadView, 
    ResumeListView, 
    ResumeDetailView, 
    ResumeAnalyzeView,
    JobSpecificAnalysisView,
    ResumeTailoringGenerateView,
    TailoringChangeReviewView,
    ResumeVersionApproveView,
    ResumeVersionDownloadView
)

urlpatterns = [
    path('', ResumeListView.as_view(), name='resume_list'),
    path('upload/', ResumeUploadView.as_view(), name='resume_upload'),
    path('<int:pk>/', ResumeDetailView.as_view(), name='resume_detail'),
    path('<int:pk>/analyze/', ResumeAnalyzeView.as_view(), name='resume_analyze'),
    path('<int:pk>/analyze/<int:job_id>/', JobSpecificAnalysisView.as_view(), name='job_analyze'),
    path('<int:pk>/tailor/', ResumeTailoringGenerateView.as_view(), name='resume_tailor_no_job'),
    path('<int:pk>/tailor/<int:job_id>/', ResumeTailoringGenerateView.as_view(), name='resume_tailor'),
    path('changes/<int:change_id>/', TailoringChangeReviewView.as_view(), name='change_review'),
    path('versions/<int:version_id>/approve/', ResumeVersionApproveView.as_view(), name='version_approve'),
    path('versions/<int:version_id>/download/', ResumeVersionDownloadView.as_view(), name='version_download'),
]
