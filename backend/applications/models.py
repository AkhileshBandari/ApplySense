from django.db import models
from django.conf import settings
from jobs.models import Job
from resumes.models import ResumeVersion

class Application(models.Model):
    STATUS_CHOICES = (
        # Preparation & Submission
        ('DRAFT', 'Draft'),
        ('PREPARING', 'Preparing'),
        ('REVIEW_REQUIRED', 'Review Required'),
        ('READY_TO_SUBMIT', 'Ready to Submit'),
        ('SUBMITTING', 'Submitting'),
        ('SUBMITTED', 'Submitted'),
        ('APPLICATION_FAILED', 'Application Failed'),
        ('WITHDRAWN', 'Withdrawn'),
        
        # Post-Submission (ATS Tracking)
        ('UNDER_REVIEW', 'Under Review'),
        ('ASSESSMENT', 'Assessment'),
        ('INTERVIEW', 'Interview'),
        ('FINAL_ROUND', 'Final Round'),
        ('OFFER', 'Offer'),
        ('REJECTED', 'Rejected'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('UNKNOWN', 'Unknown'),
        
        # Legacy/Compatibility mappings removed (data migrated to DRAFT and SUBMITTED)
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    
    # Metadata for snapshot/manual entry decoupling
    company = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=100, default='Custom')
    application_provider = models.CharField(max_length=100, blank=True, null=True)
    application_mode = models.CharField(max_length=50, blank=True, null=True)
    
    resume_version = models.ForeignKey(ResumeVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    snapshot = models.JSONField(null=True, blank=True, help_text="Immutable snapshot of Job, ResumeVersion, and CandidateContext at submission")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    preparation_status = models.CharField(max_length=30, blank=True, null=True)
    submission_status = models.CharField(max_length=30, blank=True, null=True)
    
    application_url = models.URLField(max_length=500, blank=True, null=True)
    external_identifier = models.CharField(max_length=100, blank=True, null=True)
    
    match_score = models.IntegerField(default=0)
    match_details = models.JSONField(null=True, blank=True)
    
    applied_at = models.DateTimeField(null=True, blank=True)
    prepared_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    last_status_change_at = models.DateTimeField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        pass

    def __str__(self):
        return f"{self.user.email} -> {self.role or (self.job.title if self.job else 'Unknown')} ({self.status})"

class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    source = models.CharField(max_length=50) # USER, SYSTEM, EXTENSION, ATS, IMPORT
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.id}: {self.previous_status} -> {self.new_status}"

class ApplicationQuestion(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='questions')
    question_key = models.CharField(max_length=100) # Normalized canonical key
    question_text = models.TextField()
    question_type = models.CharField(max_length=50) # TEXT, BOOLEAN, SINGLE_SELECT, etc
    category = models.CharField(max_length=50, blank=True, null=True)
    required = models.BooleanField(default=False)
    options = models.JSONField(null=True, blank=True)
    source_field_identifier = models.CharField(max_length=200, blank=True, null=True) # ID from ATS DOM
    
    answer = models.TextField(blank=True, null=True)
    answer_source = models.CharField(max_length=50, blank=True, null=True) # VERIFIED_PROFILE, ANSWER_MEMORY, USER_ENTERED, SYSTEM_DERIVED, UNANSWERED
    review_status = models.CharField(max_length=50, default='PENDING') # AUTO_RESOLVED, REVIEW_RECOMMENDED, USER_INPUT_REQUIRED, BLOCKED, APPROVED
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Q: {self.question_key} (App: {self.application.id})"

class ApplicationAnswerMemory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='answer_memory')
    question_key = models.CharField(max_length=100)
    canonical_category = models.CharField(max_length=50, blank=True, null=True)
    answer = models.TextField()
    answer_type = models.CharField(max_length=50, default='TEXT')
    source = models.CharField(max_length=50, default='USER_ENTERED')
    verification_status = models.CharField(max_length=50, default='UNVERIFIED')
    
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'question_key')

    def clean(self):
        super().clean()
        import re
        blocked_terms = [
            'PASSWORD', 'PASSCODE', 'OTP', 'ONE_TIME_PASSWORD', 'CAPTCHA',
            'AUTH_TOKEN', 'ACCESS_TOKEN', 'REFRESH_TOKEN', 'SESSION_COOKIE',
            'API_KEY', 'SECRET_KEY', 'SECURITY_CODE'
        ]
        key_upper = (self.question_key or '').upper()
        if any(term in key_upper for term in blocked_terms):
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Cannot store sensitive credential data in AnswerMemory: {self.question_key}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Memory: {self.question_key} ({self.user.email})"

class ApplicationAuditLog(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='audit_logs')
    event_type = models.CharField(max_length=50) # e.g. PREPARATION_STARTED, ANSWER_RESOLVED
    actor = models.CharField(max_length=50, default='SYSTEM')
    metadata = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit: {self.application.id} - {self.event_type}"

class AutomationPolicy(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='automation_policy')
    automation_enabled = models.BooleanField(default=False)
    require_review_before_submit = models.BooleanField(default=True)
    daily_application_limit = models.IntegerField(default=10)
    weekly_application_limit = models.IntegerField(default=50)
    minimum_match_score = models.IntegerField(default=75)
    allowed_application_modes = models.JSONField(default=list, help_text="List of allowed platform capabilities (e.g. AUTHORIZED_API_APPLY)")
    global_pause = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Policy for {self.user.email}"

class AutomationRule(models.Model):
    policy = models.ForeignKey(AutomationPolicy, on_delete=models.CASCADE, related_name='rules')
    rule_type = models.CharField(max_length=50) # EXCLUDED_COMPANY, ALLOWED_COUNTRY, EXCLUDED_COUNTRY, MINIMUM_COMPENSATION, etc.
    value = models.JSONField()
    
    def __str__(self):
        return f"Rule {self.rule_type} for {self.policy.user.email}"

class ApplicationApproval(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='approvals')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    snapshot_fingerprint = models.CharField(max_length=255)
    approved_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='VALID') # VALID, REVOKED, INVALIDATED
    
    def __str__(self):
        return f"Approval for {self.application.id} by {self.approved_by.email}"

class PolicyDecision(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='policy_decisions')
    decision = models.CharField(max_length=50) # ALLOW_PREPARATION, REQUIRE_REVIEW, BLOCK
    reason_codes = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Decision: {self.decision} for {self.application.id}"


class Interview(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    stage = models.CharField(max_length=100) # Technical, HR, System Design, etc.
    scheduled_at = models.DateTimeField()
    location_type = models.CharField(max_length=50, default='Virtual') # Virtual, On-Site
    video_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Interview for {self.application.role or 'Role'} - {self.stage}"

class ApplicationNote(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note on {self.application.id} at {self.created_at}"

class FormSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='form_sessions')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='form_sessions')
    provider = models.CharField(max_length=100) # e.g. Greenhouse, Lever, Ashby, Generic
    url = models.URLField(max_length=1000)
    status = models.CharField(max_length=50, default='DETECTED') # DETECTED, ANALYZED, PARTIALLY_FILLED, READY_FOR_REVIEW, BLOCKED, ABANDONED
    
    provider_variant = models.CharField(max_length=100, blank=True, null=True, help_text="Specific ATS variant/version detected")
    provider_confidence = models.FloatField(default=1.0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FormSession {self.id} for {self.application.id} ({self.status})"

class DetectedApplicationForm(models.Model):
    session = models.OneToOneField(FormSession, on_delete=models.CASCADE, related_name='detected_form')
    form_identifier = models.CharField(max_length=255, blank=True, null=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    # Raw JSON of the entire schema detected by the extension for debugging
    raw_schema = models.JSONField(blank=True, null=True) 

    def __str__(self):
        return f"Form Schema for Session {self.session.id}"

class DetectedApplicationFormField(models.Model):
    form = models.ForeignKey(DetectedApplicationForm, on_delete=models.CASCADE, related_name='fields')
    
    # Evidence
    provider_field_id = models.CharField(max_length=255, blank=True, null=True)
    label = models.TextField(blank=True, null=True)
    name_attribute = models.CharField(max_length=255, blank=True, null=True)
    input_type = models.CharField(max_length=100, blank=True, null=True)
    options = models.JSONField(blank=True, null=True)
    required = models.BooleanField(default=False)
    
    # Classification
    normalized_key = models.CharField(max_length=100, default='UNKNOWN')
    category = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.FloatField(default=0.0)
    
    # Resolution
    current_value = models.TextField(blank=True, null=True)
    proposed_value = models.TextField(blank=True, null=True)
    resolution_status = models.CharField(max_length=50, default='PENDING') # SAFE_AUTOFILL, REVIEW_AUTOFILL, USER_INPUT_REQUIRED, NEVER_AUTOFILL
    answer_source = models.CharField(max_length=50, blank=True, null=True)
    requires_review = models.BooleanField(default=True)

    def __str__(self):
        return f"Field {self.normalized_key} ({self.resolution_status})"

class FormSessionAuditLog(models.Model):
    session = models.ForeignKey(FormSession, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=100) # FIELD_DETECTED, FIELD_CLASSIFIED, FIELD_FILLED, FIELD_SKIPPED, USER_INPUT_REQUIRED, FILE_PREPARED, FORM_RESCAN, REVIEW_READY
    field_key = models.CharField(max_length=100, blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit {self.action} for Session {self.session.id}"

# ==========================================
# PHASE 5D - CONTROLLED EXECUTION DOMAIN
# ==========================================

class ApplicationExecution(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='executions')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='executions')
    snapshot_fingerprint = models.CharField(max_length=255)
    approval = models.ForeignKey(ApplicationApproval, on_delete=models.SET_NULL, null=True, blank=True)
    
    provider = models.CharField(max_length=100)
    application_mode = models.CharField(max_length=100) # e.g. USER_CONFIRMED_BROWSER_SUBMISSION
    execution_status = models.CharField(max_length=50, default='CREATED')
    
    policy_decision_reference = models.ForeignKey(PolicyDecision, on_delete=models.SET_NULL, null=True, blank=True)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Execution {self.id} ({self.execution_status}) - App {self.application.id}"

class SubmissionAttempt(models.Model):
    execution = models.ForeignKey(ApplicationExecution, on_delete=models.CASCADE, related_name='attempts')
    attempt_number = models.IntegerField(default=1)
    status = models.CharField(max_length=50) # STARTED, FAILED, SUCCEEDED, UNKNOWN_RESULT
    execution_mode = models.CharField(max_length=100)
    provider = models.CharField(max_length=100)
    
    error_code = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    response_metadata = models.JSONField(blank=True, null=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attempt {self.attempt_number} for Execution {self.execution.id}"

class SubmissionReceipt(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='receipts')
    execution = models.ForeignKey(ApplicationExecution, on_delete=models.CASCADE, related_name='receipts')
    provider = models.CharField(max_length=100)
    
    external_application_id = models.CharField(max_length=255, blank=True, null=True)
    external_requisition_id = models.CharField(max_length=255, blank=True, null=True)
    confirmation_reference = models.CharField(max_length=255, blank=True, null=True)
    confirmation_url = models.URLField(max_length=1000, blank=True, null=True)
    confirmation_text_fingerprint = models.CharField(max_length=255, blank=True, null=True)
    
    execution_mode = models.CharField(max_length=100)
    receipt_source = models.CharField(max_length=100) # PROVIDER_API, CONFIRMATION_PAGE, USER_CONFIRMED
    
    submitted_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt {self.id} for App {self.application.id}"
