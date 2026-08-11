from django.db import models
from django.conf import settings

class DomainStateStatus(models.TextChoices):
    HEALTHY = 'HEALTHY', 'Healthy'
    STALE = 'STALE', 'Stale'
    DEGRADED = 'DEGRADED', 'Degraded'
    BLOCKED = 'BLOCKED', 'Blocked'
    ACTION_REQUIRED = 'ACTION_REQUIRED', 'Action Required'
    AWAITING_USER = 'AWAITING_USER', 'Awaiting User'
    AI_UNAVAILABLE = 'AI_UNAVAILABLE', 'AI Unavailable'
    AUTOMATION_UNAVAILABLE = 'AUTOMATION_UNAVAILABLE', 'Automation Unavailable'
    DATA_INCOMPLETE = 'DATA_INCOMPLETE', 'Data Incomplete'
    NOT_INITIALIZED = 'NOT_INITIALIZED', 'Not Initialized'

class SystemState(models.TextChoices):
    ONBOARDING = 'ONBOARDING', 'Onboarding'
    PROFILE_READY = 'PROFILE_READY', 'Profile Ready'
    JOB_SEARCH_READY = 'JOB_SEARCH_READY', 'Job Search Ready'
    MATCHING = 'MATCHING', 'Matching'
    GAP_ANALYSIS = 'GAP_ANALYSIS', 'Gap Analysis'
    LEARNING = 'LEARNING', 'Learning'
    EVIDENCE_COLLECTION = 'EVIDENCE_COLLECTION', 'Evidence Collection'
    CAREER_BRAND_READY = 'CAREER_BRAND_READY', 'Career Brand Ready'
    INTERVIEW_PREPARATION = 'INTERVIEW_PREPARATION', 'Interview Preparation'
    PATHWAY_EXPLORATION = 'PATHWAY_EXPLORATION', 'Pathway Exploration'
    DECISION_READY = 'DECISION_READY', 'Decision Ready'
    EXECUTION_READY = 'EXECUTION_READY', 'Execution Ready'
    APPLICATION_ACTIVE = 'APPLICATION_ACTIVE', 'Application Active'
    OUTCOME_TRACKING = 'OUTCOME_TRACKING', 'Outcome Tracking'
    OPTIMIZATION = 'OPTIMIZATION', 'Optimization'
    BLOCKED = 'BLOCKED', 'Blocked'
    ACTION_REQUIRED = 'ACTION_REQUIRED', 'Action Required'
    DEGRADED = 'DEGRADED', 'Degraded'

class SystemBlocker(models.TextChoices):
    MISSING_VERIFIED_SKILL = 'MISSING_VERIFIED_SKILL', 'Missing Verified Skill'
    MISSING_EVIDENCE = 'MISSING_EVIDENCE', 'Missing Evidence'
    RESUME_INCOMPLETE = 'RESUME_INCOMPLETE', 'Resume Incomplete'
    PROFILE_INCONSISTENT = 'PROFILE_INCONSISTENT', 'Profile Inconsistent'
    INTERVIEW_GAP = 'INTERVIEW_GAP', 'Interview Gap'
    APPLICATION_DATA_MISSING = 'APPLICATION_DATA_MISSING', 'Application Data Missing'
    AUTHENTICATION_REQUIRED = 'AUTHENTICATION_REQUIRED', 'Authentication Required'
    CONSENT_REQUIRED = 'CONSENT_REQUIRED', 'Consent Required'
    CAPTCHA_REQUIRED = 'CAPTCHA_REQUIRED', 'CAPTCHA Required'
    USER_ACTION_REQUIRED = 'USER_ACTION_REQUIRED', 'User Action Required'
    ENTITLEMENT_BLOCKED = 'ENTITLEMENT_BLOCKED', 'Entitlement Blocked'
    PROVIDER_UNSUPPORTED = 'PROVIDER_UNSUPPORTED', 'Provider Unsupported'
    GLOBAL_PAUSE = 'GLOBAL_PAUSE', 'Global Pause'
    SYSTEM_DEGRADED = 'SYSTEM_DEGRADED', 'System Degraded'
    STALE_DOMAIN = 'STALE_DOMAIN', 'Stale Domain'

class DomainName(models.TextChoices):
    CONTEXT = 'CONTEXT', 'Candidate Context'
    SKILL_GAP = 'SKILL_GAP', 'Skill Gap'
    LEARNING = 'LEARNING', 'Learning Roadmap'
    EVIDENCE = 'EVIDENCE', 'Evidence'
    BRAND = 'BRAND', 'Career Brand'
    INTERVIEW = 'INTERVIEW', 'Interview Intelligence'
    PATHWAY = 'PATHWAY', 'Career Pathway'
    DECISION = 'DECISION', 'Career Decision'
    EXECUTION = 'EXECUTION', 'Career Execution'
    ANALYTICS = 'ANALYTICS', 'Application Analytics'

class CareerOperatingState(models.Model):
    """The overarching holistic system state for a candidate."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='operating_state')
    
    overall_readiness_score = models.IntegerField(default=0)
    current_primary_goal = models.CharField(max_length=255, blank=True)
    top_blocker = models.CharField(max_length=255, blank=True)
    
    execution_velocity_score = models.IntegerField(default=0)
    application_momentum_score = models.IntegerField(default=0)
    
    current_os_state = models.CharField(max_length=50, choices=SystemState.choices, default=SystemState.ONBOARDING)
    overall_health = models.CharField(max_length=50, choices=DomainStateStatus.choices, default=DomainStateStatus.NOT_INITIALIZED)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CareerDomainState(models.Model):
    """The operating status of a specific integration domain."""
    operating_state = models.ForeignKey(CareerOperatingState, on_delete=models.CASCADE, related_name='domains')
    domain_name = models.CharField(max_length=50, choices=DomainName.choices)
    status = models.CharField(max_length=50, choices=DomainStateStatus.choices, default=DomainStateStatus.NOT_INITIALIZED)
    
    # Store source checksum or version ID to detect staleness
    source_version_hash = models.CharField(max_length=255, blank=True)
    last_synced_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('operating_state', 'domain_name')

class DataTrustLevel(models.TextChoices):
    VERIFIED = 'VERIFIED', 'Verified Facts'
    DERIVED = 'DERIVED', 'Derived Intelligence'
    HYPOTHETICAL = 'HYPOTHETICAL', 'Hypothetical Scenario'
    ADVISORY = 'ADVISORY', 'Advisory Recommendation'
    UNVERIFIED = 'UNVERIFIED', 'Unverified'
    STALE = 'STALE', 'Stale'

class UserActionItem(models.Model):
    """Unified user-action queue for Phase 10 User Action Center."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='os_actions')
    source_domain = models.CharField(max_length=50, choices=DomainName.choices)
    blocker_type = models.CharField(max_length=50, choices=SystemBlocker.choices)
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.IntegerField(default=0) # Higher = more urgent
    is_resolved = models.BooleanField(default=False)
    
    # Context specific data (e.g. which skill is missing, which application requires captcha)
    context_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']

class CareerIntegrationSnapshot(models.Model):
    """Immutable, deterministic point-in-time snapshot of the system state."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='integration_snapshots')
    
    payload = models.JSONField()
    snapshot_hash = models.CharField(max_length=255)
    trust_level_map = models.JSONField(default=dict) # e.g. {"context": "VERIFIED", "scenario": "HYPOTHETICAL"}
    
    created_at = models.DateTimeField(auto_now_add=True)

class CanonicalOutcomeEvent(models.TextChoices):
    APPLICATION_SUBMITTED = 'APPLICATION_SUBMITTED', 'Application Submitted'
    APPLICATION_REJECTED = 'APPLICATION_REJECTED', 'Application Rejected'
    APPLICATION_INTERVIEW = 'APPLICATION_INTERVIEW', 'Application Interview'
    APPLICATION_FINAL_ROUND = 'APPLICATION_FINAL_ROUND', 'Application Final Round'
    APPLICATION_OFFER = 'APPLICATION_OFFER', 'Application Offer'
    APPLICATION_ACCEPTED = 'APPLICATION_ACCEPTED', 'Application Accepted'
    
    INTERVIEW_COMPLETED = 'INTERVIEW_COMPLETED', 'Interview Completed'
    INTERVIEW_WEAKNESS_IDENTIFIED = 'INTERVIEW_WEAKNESS_IDENTIFIED', 'Interview Weakness Identified'
    
    SKILL_VERIFIED = 'SKILL_VERIFIED', 'Skill Verified'
    SKILL_GAP_CLOSED = 'SKILL_GAP_CLOSED', 'Skill Gap Closed'
    
    EVIDENCE_VERIFIED = 'EVIDENCE_VERIFIED', 'Evidence Verified'
    CAREER_BRAND_UPDATED = 'CAREER_BRAND_UPDATED', 'Career Brand Updated'
    
    CAREER_DECISION_CHANGED = 'CAREER_DECISION_CHANGED', 'Career Decision Changed'
    CAREER_EXECUTION_COMPLETED = 'CAREER_EXECUTION_COMPLETED', 'Career Execution Completed'

class CareerOutcomeEvent(models.Model):
    """Append-only consequential outcome events mapped from specific sub-systems."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='career_outcomes')
    event_type = models.CharField(max_length=100, choices=CanonicalOutcomeEvent.choices)
    source_domain = models.CharField(max_length=50, choices=DomainName.choices)
    
    # Optional references
    source_object_id = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict)
    
    timestamp = models.DateTimeField(auto_now_add=True)

class CareerReconciliationRecord(models.Model):
    """Idempotency tracking for reconciliation runs."""
    event = models.OneToOneField(CareerOutcomeEvent, on_delete=models.CASCADE, related_name='reconciliation')
    domains_marked_stale = models.JSONField(default=list)
    reconciled_at = models.DateTimeField(auto_now_add=True)
