from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from services.career_ops.views import (
    CareerOpsDiscoverView,
    CareerOpsEvaluateView,
    CareerOpsRecommendView,
    CareerOpsTailorView,
)

from applysense import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/liveness/', core_views.health_liveness, name='health_liveness'),
    path('api/health/readiness/', core_views.health_readiness, name='health_readiness'),
    path('api/health/automation/', core_views.health_automation, name='health_automation'),
    path('api/auth/', include('authentication.urls')),
    path('api/profile/', include('profiles.urls')),
    path('api/resumes/', include('resumes.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/automation/', include('automation.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/coach/', include('ai_engine.urls')),
    path('api/copilot/', include('copilot.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/evidence/', include('evidence.urls')),
    path('api/career-brand/', include('career_brand.urls')),
    path('api/interview-intelligence/', include('interviews.urls')),
    path('api/career-pathways/', include('career_pathways.urls')),
    path('api/career-decisions/', include('career_decisions.urls')),
    path('api/career-execution/', include('career_execution.urls')),
    path('api/career-integration/', include('career_integration.urls')),
    path('api/career-outcomes/', include('career_outcomes.urls')),
    path('api/services/career-ops/', include('services.career_ops.urls')),
    path('api/jobs/discover', CareerOpsDiscoverView.as_view(), name='career_ops_discover'),
    path('api/jobs/discover/', CareerOpsDiscoverView.as_view(), name='career_ops_discover_slash'),
    path('api/jobs/evaluate', CareerOpsEvaluateView.as_view(), name='career_ops_evaluate'),
    path('api/jobs/evaluate/', CareerOpsEvaluateView.as_view(), name='career_ops_evaluate_slash'),
    path('api/jobs/recommend', CareerOpsRecommendView.as_view(), name='career_ops_recommend'),
    path('api/jobs/recommend/', CareerOpsRecommendView.as_view(), name='career_ops_recommend_slash'),
    path('api/resume/tailor', CareerOpsTailorView.as_view(), name='career_ops_tailor'),
    path('api/resume/tailor/', CareerOpsTailorView.as_view(), name='career_ops_tailor_slash'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
