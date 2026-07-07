from django.urls import path
from .views import ResumeUploadView, ResumeListView, ResumeDetailView, ResumeTailorView

urlpatterns = [
    path('', ResumeListView.as_view(), name='resume_list'),
    path('upload/', ResumeUploadView.as_view(), name='resume_upload'),
    path('<int:pk>/', ResumeDetailView.as_view(), name='resume_detail'),
    path('<int:pk>/tailor/', ResumeTailorView.as_view(), name='resume_tailor'),
]
