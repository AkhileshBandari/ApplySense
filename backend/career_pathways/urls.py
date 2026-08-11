from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CareerPathViewSet, CareerPathRecommendationView, CareerPathScenarioViewSet

router = DefaultRouter()
router.register(r'paths', CareerPathViewSet, basename='careerpath')
router.register(r'scenarios', CareerPathScenarioViewSet, basename='scenario')

urlpatterns = [
    path('', include(router.urls)),
    path('recommendations/', CareerPathRecommendationView.as_view(), name='path-recommendations'),
]
