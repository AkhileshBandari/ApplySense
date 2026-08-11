from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import (
    Profile, Experience, Education, Certification, Skill,
    Project, Achievement, Language, CareerPreferences, WorkAuthorization, VerificationStatus
)
from .serializers import (
    ProfileSerializer, ExperienceSerializer, 
    EducationSerializer, CertificationSerializer, SkillSerializer,
    ProjectSerializer, AchievementSerializer, LanguageSerializer,
    CareerPreferencesSerializer, WorkAuthorizationSerializer
)
from .services.candidate_context import CandidateContextService
from .services.merge_service import MergeService

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
        serializer.save(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class ExperienceViewSet(BaseProfileSubViewSet):
    serializer_class = ExperienceSerializer
    def get_queryset(self): return Experience.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class EducationViewSet(BaseProfileSubViewSet):
    serializer_class = EducationSerializer
    def get_queryset(self): return Education.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class CertificationViewSet(BaseProfileSubViewSet):
    serializer_class = CertificationSerializer
    def get_queryset(self): return Certification.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class SkillViewSet(BaseProfileSubViewSet):
    serializer_class = SkillSerializer
    def get_queryset(self): return Skill.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED).order_by('id')

class ProjectViewSet(BaseProfileSubViewSet):
    serializer_class = ProjectSerializer
    def get_queryset(self): return Project.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class AchievementViewSet(BaseProfileSubViewSet):
    serializer_class = AchievementSerializer
    def get_queryset(self): return Achievement.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class LanguageViewSet(BaseProfileSubViewSet):
    serializer_class = LanguageSerializer
    def get_queryset(self): return Language.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class WorkAuthorizationViewSet(BaseProfileSubViewSet):
    serializer_class = WorkAuthorizationSerializer
    def get_queryset(self): return WorkAuthorization.objects.filter(profile=self.get_profile(), verification_status=VerificationStatus.VERIFIED)

class CareerPreferencesView(generics.RetrieveUpdateAPIView):
    serializer_class = CareerPreferencesSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        pref, _ = CareerPreferences.objects.get_or_create(profile=profile)
        return pref

class ProfileCompletenessView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request):
        completeness = CandidateContextService.calculate_completeness(request.user)
        return Response(completeness)

class PendingImportView(APIView):
    """Fetches all UNVERIFIED facts belonging to a user (usually from a parsed resume)."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        profile = request.user.profile
        return Response({
            "experiences": ExperienceSerializer(Experience.objects.filter(profile=profile, verification_status=VerificationStatus.UNVERIFIED), many=True).data,
            "educations": EducationSerializer(Education.objects.filter(profile=profile, verification_status=VerificationStatus.UNVERIFIED), many=True).data,
            "skills": SkillSerializer(Skill.objects.filter(profile=profile, verification_status=VerificationStatus.UNVERIFIED), many=True).data,
            "projects": ProjectSerializer(Project.objects.filter(profile=profile, verification_status=VerificationStatus.UNVERIFIED), many=True).data,
            "certifications": CertificationSerializer(Certification.objects.filter(profile=profile, verification_status=VerificationStatus.UNVERIFIED), many=True).data,
            "languages": LanguageSerializer(Language.objects.filter(profile=profile, verification_status=VerificationStatus.UNVERIFIED), many=True).data,
        })

class FactReviewView(APIView):
    """Endpoint for accepting, editing, or rejecting UNVERIFIED facts."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        action = request.data.get('action') # 'ACCEPT', 'REJECT', 'EDIT'
        fact_type = request.data.get('fact_type')
        fact_id = request.data.get('fact_id')
        update_data = request.data.get('update_data', {})

        model_map = {
            'experience': Experience,
            'education': Education,
            'skill': Skill,
            'project': Project,
            'certification': Certification,
            'language': Language
        }

        if fact_type not in model_map:
            return Response({"error": "Invalid fact type"}, status=status.HTTP_400_BAD_REQUEST)

        model_class = model_map[fact_type]

        if action == 'ACCEPT':
            success, obj = MergeService.accept_fact(request.user, model_class, fact_id)
        elif action == 'REJECT':
            success, obj = MergeService.reject_fact(request.user, model_class, fact_id)
        elif action == 'EDIT':
            success, obj = MergeService.edit_fact(request.user, model_class, fact_id, update_data)
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        if not success:
            return Response({"error": "Fact not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"status": "success", "action": action, "id": obj.id})
