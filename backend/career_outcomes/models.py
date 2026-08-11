from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class NormalizedOutcomeState(models.TextChoices):
    APPLIED = 'APPLIED', 'Applied'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    SCREENING = 'SCREENING', 'Screening'
    ASSESSMENT = 'ASSESSMENT', 'Assessment'
    INTERVIEW = 'INTERVIEW', 'Interview'
    FINAL_ROUND = 'FINAL_ROUND', 'Final Round'
    OFFER = 'OFFER', 'Offer'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    REJECTED = 'REJECTED', 'Rejected'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    NO_RESPONSE = 'NO_RESPONSE', 'No Response'
    UNKNOWN = 'UNKNOWN', 'Unknown'

class OutcomeConfidence(models.TextChoices):
    VERY_LOW = 'VERY_LOW', 'Very Low'
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    VERY_HIGH = 'VERY_HIGH', 'Very High'

class OutcomeSourceType(models.TextChoices):
    SYSTEM_CONFIRMED = 'SYSTEM_CONFIRMED', 'System Confirmed'
    USER_CONFIRMED = 'USER_CONFIRMED', 'User Confirmed'
    PROVIDER_CONFIRMED = 'PROVIDER_CONFIRMED', 'Provider Confirmed'
    INFERRED = 'INFERRED', 'Inferred'
    UNKNOWN = 'UNKNOWN', 'Unknown'

class CareerOutcomeRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outcome_records')
    normalized_state = models.CharField(max_length=50, choices=NormalizedOutcomeState.choices, db_index=True)
    
    # Authoritative Event linkage
    source_event_id = models.CharField(max_length=255, null=True, blank=True)
    outcome_source = models.CharField(max_length=50, choices=OutcomeSourceType.choices, default=OutcomeSourceType.UNKNOWN)
    
    # Timestamps
    occurred_at = models.DateTimeField(null=True, blank=True)
    detected_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Subsystem linkages for attribution
    application_id = models.IntegerField(null=True, blank=True) # ID of Application Record
    job_id = models.IntegerField(null=True, blank=True)         # ID of Job
    resume_version_id = models.IntegerField(null=True, blank=True) # ID of ResumeVersion
    tailoring_version_id = models.IntegerField(null=True, blank=True) # ID of tailored resume
    job_match_score = models.IntegerField(null=True, blank=True)
    target_role = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    provider = models.CharField(max_length=100, null=True, blank=True)
    source_platform = models.CharField(max_length=100, null=True, blank=True)
    
    # Trust bounds
    confidence = models.CharField(max_length=50, choices=OutcomeConfidence.choices, default=OutcomeConfidence.LOW)
    verification_status = models.CharField(max_length=50, default='UNVERIFIED') # e.g. VERIFIED
    
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'normalized_state']),
            models.Index(fields=['resume_version_id']),
            models.Index(fields=['application_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.normalized_state} at {self.detected_at}"

class CareerOutcomeSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outcome_snapshots')
    snapshot_hash = models.CharField(max_length=64, unique=True)
    
    funnel_metrics = models.JSONField(default=dict)
    performance_metrics = models.JSONField(default=dict)
    comparison_groups = models.JSONField(default=dict)
    recommendation_inputs = models.JSONField(default=dict)
    
    confidence = models.CharField(max_length=50, choices=OutcomeConfidence.choices)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Snapshot {self.snapshot_hash} for {self.user.username}"
