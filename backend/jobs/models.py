from django.db import models
from django.conf import settings
from django.utils import timezone

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=150, blank=True, null=True)
    work_mode = models.CharField(max_length=50, blank=True, null=True) # Remote, Hybrid, On-site
    employment_type = models.CharField(max_length=50, blank=True, null=True) # Full-time, Contract, etc.
    
    source = models.CharField(max_length=100, default='Custom') # Legacy primary source
    application_provider = models.CharField(max_length=100, blank=True, null=True) # e.g. Greenhouse, Workday
    
    canonical_hash = models.CharField(max_length=255, blank=True, null=True, db_index=True, help_text="Normalized identity for deduplication")
    
    country = models.CharField(max_length=150, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    region = models.CharField(max_length=150, blank=True, null=True)
    is_remote_worldwide = models.BooleanField(default=False)
    work_authorization_required = models.BooleanField(default=True)
    sponsorship_available = models.BooleanField(default=False)
    
    source_url = models.URLField(max_length=500, blank=True, null=True, unique=True)
    source_job_id = models.CharField(max_length=100, blank=True, null=True)
    application_url = models.URLField(max_length=500, blank=True, null=True)
    
    description = models.TextField()
    requirements = models.JSONField(null=True, blank=True)
    
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True, null=True, default='USD')
    salary_period = models.CharField(max_length=20, blank=True, null=True, default='YEARLY')
    
    experience_min = models.IntegerField(null=True, blank=True)
    experience_max = models.IntegerField(null=True, blank=True)
    seniority = models.CharField(max_length=100, blank=True, null=True)
    
    industry = models.CharField(max_length=150, blank=True, null=True)
    department = models.CharField(max_length=150, blank=True, null=True)
    
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('STALE', 'Stale'),
        ('CLOSED', 'Closed'),
        ('UNKNOWN', 'Unknown'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    discovered_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(auto_now=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

class JobRequirement(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='requirements_norm')
    required_skills = models.JSONField(default=list)
    preferred_skills = models.JSONField(default=list)
    minimum_experience = models.IntegerField(null=True, blank=True)
    education_requirements = models.JSONField(default=list)
    responsibilities = models.JSONField(default=list)

    def __str__(self):
        return f"Requirements for {self.job.title}"

class JobMatch(models.Model):
    ELIGIBILITY_CHOICES = (
        ('ELIGIBLE', 'Eligible'),
        ('POSSIBLY_ELIGIBLE', 'Possibly Eligible'),
        ('STRETCH', 'Stretch'),
        ('LIKELY_INELIGIBLE', 'Likely Ineligible'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='matches')
    
    overall_score = models.IntegerField(default=0)
    eligibility = models.CharField(max_length=30, choices=ELIGIBILITY_CHOICES, default='POSSIBLY_ELIGIBLE')
    
    dimension_scores = models.JSONField(default=dict)
    missing_required = models.JSONField(default=list)
    missing_preferred = models.JSONField(default=list)
    candidate_preference_conflicts = models.JSONField(default=list)
    
    algorithm_version = models.CharField(max_length=50, default='1.0')
    created_at = models.DateTimeField(auto_now=True) # Update timestamp on recalculation
    
    class Meta:
        unique_together = ('user', 'job')
        
    def __str__(self):
        return f"Match {self.overall_score}% for {self.user} -> {self.job}"

class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='savers')
    notes = models.TextField(blank=True, null=True)
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'job')
        
    def __str__(self):
        return f"{self.user} saved {self.job}"

class JobSourceOccurrence(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='occurrences')
    source = models.CharField(max_length=100) # e.g. LinkedIn, Indeed
    source_url = models.URLField(max_length=1000)
    source_job_id = models.CharField(max_length=100, blank=True, null=True)
    discovered_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Cannot strictly enforce uniqueness on just source_job_id if it's blank, so we allow duplicates if no ID
        constraints = [
            models.UniqueConstraint(fields=['source', 'source_job_id'], name='unique_source_job_id', condition=models.Q(source_job_id__isnull=False) & ~models.Q(source_job_id=""))
        ]

    def __str__(self):
        return f"{self.source} occurrence for {self.job.title}"

