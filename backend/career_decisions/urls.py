from django.urls import path, include
from rest_framework.routers import DefaultRouter
from career_decisions.views import CareerDecisionViewSet, CareerActionViewSet

router = DefaultRouter()
router.register(r'actions', CareerActionViewSet, basename='career-action')
router.register(r'', CareerDecisionViewSet, basename='career-decision')

urlpatterns = [
    path('', include(router.urls)),
]
