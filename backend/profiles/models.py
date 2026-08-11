from django.db import models
from django.conf import settings

class ProvenanceSource(models.TextChoices):
    USER_VERIFIED = 'USER_VERIFIED', 'User Verified'
    RESUME_IMPORTED = 'RESUME_IMPORTED', 'Resume Imported'
    EXTERNAL_IMPORTED = 'EXTERNAL_IMPORTED', 'External Imported'
    AI_INFERRED = 'AI_INFERRED', 'AI Inferred'

class VerificationStatus(models.TextChoices):
    UNVERIFIED = 'UNVERIFIED', 'Unverified'
    VERIFIED = 'VERIFIED', 'Verified'
    REJECTED = 'REJECTED', 'Rejected'

class ProvenanceMixin(models.Model):
    source = models.CharField(max_length=50, choices=ProvenanceSource.choices, default=ProvenanceSource.USER_VERIFIED)
    verification_status = models.CharField(max_length=50, choices=VerificationStatus.choices, default=VerificationStatus.VERIFIED)
    source_resume = models.ForeignKey('resumes.Resume', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        abstract = True

class Profile(ProvenanceMixin, models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=150, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    
    # Extra Profile specific fields as per Phase 2
    professional_headline = models.CharField(max_length=200, blank=True)
    career_goals = models.TextField(blank=True)
    experience_level = models.CharField(max_length=50, blank=True) # e.g. entry, mid, senior

    def __str__(self):
        return f"Profile of {self.user.email}"

class Experience(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.role} at {self.company}"

class Education(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=150)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=150)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True) # Per spec

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} from {self.institution}"

class Certification(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=150)
    issuing_organization = models.CharField(max_length=150)
    issue_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    credential_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} from {self.issuing_organization}"

class Skill(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True) # Optional category

    def __str__(self):
        return self.name

class Project(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    technologies = models.CharField(max_length=255, blank=True) # comma separated or similar
    link = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Achievement(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='achievements')
    description = models.TextField()

    def __str__(self):
        return self.description[:50]

class Language(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

class CareerPreferences(ProvenanceMixin, models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='preferences')
    preferred_roles = models.CharField(max_length=255, blank=True)
    preferred_locations = models.CharField(max_length=255, blank=True)
    preferred_industries = models.CharField(max_length=255, blank=True)
    job_type = models.CharField(max_length=100, blank=True) # full-time, contract, etc
    remote_preference = models.CharField(max_length=50, blank=True) # remote, hybrid, onsite
    expected_compensation_min = models.IntegerField(null=True, blank=True)
    expected_compensation_max = models.IntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    notice_period = models.CharField(max_length=50, blank=True)
    available_from = models.DateField(null=True, blank=True)
    relocation_willingness = models.BooleanField(default=False)

    def __str__(self):
        return f"Preferences for {self.profile.user.email}"

class WorkAuthorization(ProvenanceMixin, models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='work_authorizations')
    country = models.CharField(max_length=100)
    status = models.CharField(max_length=100) # Citizen, Permanent Resident, Visa
    sponsorship_required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.country} - {self.status} for {self.profile.user.email}"