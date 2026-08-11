from django.urls import path

from .views import (
    CareerOpsDiscoverView,
    CareerOpsEvaluateView,
    CareerOpsRecommendView,
    CareerOpsTailorView,
)

urlpatterns = [
    path('discover/', CareerOpsDiscoverView.as_view(), name='career_ops_discover'),
    path('evaluate/', CareerOpsEvaluateView.as_view(), name='career_ops_evaluate'),
    path('recommend/', CareerOpsRecommendView.as_view(), name='career_ops_recommend'),
    path('tailor/', CareerOpsTailorView.as_view(), name='career_ops_tailor'),
]
