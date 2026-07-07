from django.urls import path
from .views import JobParseView, JobRecommendationView, JobDetailView

urlpatterns = [
    path('parse/', JobParseView.as_view(), name='job_parse'),
    path('recommendations/', JobRecommendationView.as_view(), name='job_recommendations'),
    path('<int:pk>/', JobDetailView.as_view(), name='job_detail'),
]
