from django.urls import path, include
from rest_framework.routers import DefaultRouter
from career_execution.views import CareerExecutionViewSet, CareerExecutionItemViewSet

router = DefaultRouter()
router.register(r'items', CareerExecutionItemViewSet, basename='career-execution-item')
router.register(r'', CareerExecutionViewSet, basename='career-execution')

urlpatterns = [
    path('', include(router.urls)),
]
