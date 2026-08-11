from django.db import models
from django.conf import settings

class ProfessionalProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='professional_profiles')
    provider = models.CharField(max_length=50, default='MANUAL') # MANUAL, LINKEDIN_EXPORT, etc.
    external_profile_id = models.CharField(max_length=255, blank=True, null=True)
    profile_url = models.URLField(blank=True, null=True)
    
    headline = models.CharField(max_length=255, blank=True)
    about = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    current_role = models.CharField(max_length=255, blank=True)
    target_role = models.CharField(max_length=255, blank=True)
    
    source = models.CharField(max_length=50, default='USER_ENTERED')
    sync_status = models.CharField(max_length=50, default='IDLE')
    last_synced_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.provider} Profile"

class ProfessionalProfileSection(models.Model):
    SECTION_TYPES = (
        ('HEADLINE', 'Headline'),
        ('ABOUT', 'About'),
        ('EXPERIENCE', 'Experience'),
        ('PROJECT', 'Project'),
        ('SKILL', 'Skill'),
        ('EDUCATION', 'Education'),
        ('CERTIFICATION', 'Certification'),
        ('VOLUNTEERING', 'Volunteering'),
        ('AWARD', 'Award'),
        ('PUBLICATION', 'Publication'),
        ('OTHER', 'Other'),
    )

    profile = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=50, choices=SECTION_TYPES)
    position = models.IntegerField(default=0)
    raw_content = models.TextField(blank=True)
    structured_content = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=50, default='USER_ENTERED')
    verification_status = models.CharField(max_length=50, default='UNVERIFIED') # UNVERIFIED, SUPPORTED, UNSUPPORTED, CONFLICTING
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.profile.user.username} - {self.section_type}"

class ProfessionalProfileAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_analyses')
    profile = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='analyses')
    target_role = models.CharField(max_length=255, blank=True)
    target_job_id = models.CharField(max_length=255, blank=True, null=True) # Reference to Phase 4 Job if specified
    
    overall_score = models.IntegerField(default=0)
    completeness_score = models.IntegerField(default=0)
    evidence_alignment_score = models.IntegerField(default=0)
    keyword_alignment_score = models.IntegerField(default=0)
    consistency_score = models.IntegerField(default=0)
    recruiter_readiness_score = models.IntegerField(default=0)
    
    analysis_version = models.CharField(max_length=50, default='1.0')
    snapshot = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

class ProfessionalProfileRecommendation(models.Model):
    SEVERITY_CHOICES = (
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EDITED', 'Edited'),
    )

    analysis = models.ForeignKey(ProfessionalProfileAnalysis, on_delete=models.CASCADE, related_name='recommendations')
    section_type = models.CharField(max_length=50, choices=ProfessionalProfileSection.SECTION_TYPES, blank=True)
    
    recommendation_type = models.CharField(max_length=50) # e.g., MISSING_VERIFIED_SKILL, UNSUPPORTED_PROFILE_CLAIM
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    reason_code = models.CharField(max_length=100)
    explanation = models.TextField()
    
    current_text = models.TextField(blank=True)
    proposed_text = models.TextField(blank=True)
    evidence_refs = models.JSONField(default=list, blank=True) # References to CandidateContext or Evidence IDs
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProfessionalProfileVersion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_versions')
    profile = models.ForeignKey(ProfessionalProfile, on_delete=models.SET_NULL, null=True, related_name='versions')
    target_role = models.CharField(max_length=255, blank=True)
    target_job_id = models.CharField(max_length=255, blank=True, null=True)
    
    structured_content = models.JSONField(default=dict)
    source_analysis = models.ForeignKey(ProfessionalProfileAnalysis, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

