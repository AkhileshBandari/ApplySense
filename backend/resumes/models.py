from django.db import models
from django.conf import settings
from jobs.models import Job

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/')
    file_name = models.CharField(max_length=255)
    
    STATUS_CHOICES = (
        ('UPLOADED', 'Uploaded'),
        ('EXTRACTING', 'Extracting'),
        ('PARSING', 'Parsing'),
        ('REVIEW_REQUIRED', 'Review Required'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPLOADED')
    parsing_error = models.TextField(blank=True)
    parsed_text = models.TextField(blank=True)
    health_score = models.IntegerField(null=True, blank=True)
    ats_score = models.IntegerField(null=True, blank=True)
    parsed_data = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} uploaded by {self.user.email}"

class ResumeAnalysis(models.Model):
    ANALYSIS_CHOICES = (
        ('GENERAL', 'General'),
        ('JOB_SPECIFIC', 'Job Specific'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='analyses')
    target_job = models.ForeignKey(Job, null=True, blank=True, on_delete=models.SET_NULL)
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_CHOICES)
    overall_score = models.IntegerField(null=True, blank=True)
    calculation_version = models.CharField(max_length=50)
    structured_results = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default='COMPLETE')
    created_at = models.DateTimeField(auto_now_add=True)

class ResumeVersion(models.Model):
    VERSION_STATUS = (
        ('DRAFT', 'Draft'),
        ('REVIEW_REQUIRED', 'Review Required'),
        ('APPROVED', 'Approved'),
        ('ARCHIVED', 'Archived'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    source_resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='versions')
    target_job = models.ForeignKey(Job, null=True, blank=True, on_delete=models.SET_NULL)
    version_name = models.CharField(max_length=100)
    structured_content = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=VERSION_STATUS, default='DRAFT')
    is_locked = models.BooleanField(default=False, help_text="Locked versions cannot be modified, preserving historical integrity.")
    created_at = models.DateTimeField(auto_now_add=True)

class TailoringChange(models.Model):
    VALIDATION_CHOICES = (
        ('SUPPORTED', 'Supported'),
        ('SUPPORTED_REPHRASE', 'Supported Rephrase'),
        ('AMBIGUOUS', 'Ambiguous'),
        ('UNSUPPORTED', 'Unsupported'),
    )
    USER_DECISIONS = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EDITED', 'Edited'),
    )
    version = models.ForeignKey(ResumeVersion, on_delete=models.CASCADE, related_name='changes')
    section = models.CharField(max_length=50)
    original_text = models.TextField(blank=True)
    proposed_text = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    validation_status = models.CharField(max_length=20, choices=VALIDATION_CHOICES)
    user_decision = models.CharField(max_length=20, choices=USER_DECISIONS, default='PENDING')
