from rest_framework import serializers
from .models import (
    Profile, Experience, Education, Certification, Skill, 
    Project, Achievement, Language, CareerPreferences, WorkAuthorization
)

class ProvenanceSerializerMixin(serializers.ModelSerializer):
    class Meta:
        abstract = True
        read_only_fields = ('id', 'profile', 'source', 'verification_status', 'source_resume')

class ExperienceSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = Experience
        fields = '__all__'

class EducationSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = Education
        fields = '__all__'

class CertificationSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = Certification
        fields = '__all__'

class SkillSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = Skill
        fields = '__all__'

class ProjectSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = Project
        fields = '__all__'

class AchievementSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = Achievement
        fields = '__all__'

class LanguageSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = Language
        fields = '__all__'

class CareerPreferencesSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = CareerPreferences
        fields = '__all__'

class WorkAuthorizationSerializer(ProvenanceSerializerMixin):
    class Meta(ProvenanceSerializerMixin.Meta):
        model = WorkAuthorization
        fields = '__all__'

class ProfileSerializer(ProvenanceSerializerMixin):
    experiences = serializers.SerializerMethodField()
    educations = serializers.SerializerMethodField()
    certifications = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    preferences = serializers.SerializerMethodField()
    work_authorizations = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta(ProvenanceSerializerMixin.Meta):
        model = Profile
        fields = ('id', 'user_email', 'name', 'phone', 'location', 
                  'linkedin_url', 'github_url', 'portfolio_url', 'bio',
                  'professional_headline', 'career_goals', 'experience_level',
                  'experiences', 'educations', 'certifications', 'skills',
                  'projects', 'achievements', 'languages', 'preferences',
                  'work_authorizations', 'source', 'verification_status', 'source_resume')

    # Exclude UNVERIFIED facts from the main Profile endpoint by default if needed,
    # but the frontend might want to see them. Wait, Step 8 says:
    # "DO NOT automatically populate verified Profile... records after parsing."
    # The requirement is that unverified facts are kept separate.
    # We can filter them out in the serializer or let the frontend filter.
    # It's safer to filter out UNVERIFIED in the serializer, and have a separate endpoint for pending facts.
    
    def get_verified_only(self, queryset):
        return queryset.filter(verification_status='VERIFIED')

    def get_experiences(self, obj):
        return ExperienceSerializer(self.get_verified_only(obj.experiences), many=True).data
    
    def get_educations(self, obj):
        return EducationSerializer(self.get_verified_only(obj.educations), many=True).data

    def get_certifications(self, obj):
        return CertificationSerializer(self.get_verified_only(obj.certifications), many=True).data

    def get_skills(self, obj):
        return SkillSerializer(self.get_verified_only(obj.skills), many=True).data

    def get_projects(self, obj):
        return ProjectSerializer(self.get_verified_only(obj.projects), many=True).data

    def get_achievements(self, obj):
        return AchievementSerializer(self.get_verified_only(obj.achievements), many=True).data

    def get_languages(self, obj):
        return LanguageSerializer(self.get_verified_only(obj.languages), many=True).data

    def get_preferences(self, obj):
        if hasattr(obj, 'preferences') and obj.preferences.verification_status == 'VERIFIED':
            return CareerPreferencesSerializer(obj.preferences).data
        return None

    def get_work_authorizations(self, obj):
        return WorkAuthorizationSerializer(self.get_verified_only(obj.work_authorizations), many=True).data
