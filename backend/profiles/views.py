from rest_framework import generics, viewsets, permissions
from .models import Profile, Experience, Education, Certification
from .serializers import (
    ProfileSerializer, ExperienceSerializer, 
    EducationSerializer, CertificationSerializer, SkillSerializer
)

class ProfileRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

class BaseProfileSubViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get_profile(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def perform_create(self, serializer):
        serializer.save(profile=self.get_profile())

class ExperienceViewSet(BaseProfileSubViewSet):
    serializer_class = ExperienceSerializer

    def get_queryset(self):
        return Experience.objects.filter(profile=self.get_profile())

class EducationViewSet(BaseProfileSubViewSet):
    serializer_class = EducationSerializer

    def get_queryset(self):
        return Education.objects.filter(profile=self.get_profile())

class CertificationViewSet(BaseProfileSubViewSet):
    serializer_class = CertificationSerializer

    def get_queryset(self):
        return Certification.objects.filter(profile=self.get_profile())

class SkillViewSet(BaseProfileSubViewSet):
    serializer_class = SkillSerializer

    # def get_queryset(self):
    #     return Skill.objects.filter(profile=self.get_profile())
