from django.db import models
from django.conf import settings
from jobs.models import Job
from applications.models import Application

class AutoApplyConfiguration(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auto_apply_config')
    auto_apply_enabled = models.BooleanField(default=False)
    
    # Overrides/Extensions of AutomationPolicy specifically for server apply
    daily_application_limit = models.IntegerField(null=True, blank=True)
    weekly_application_limit = models.IntegerField(null=True, blank=True)
    
    target_roles = models.JSONField(default=list, blank=True)
    excluded_roles = models.JSONField(default=list, blank=True)
    target_locations = models.JSONField(default=list, blank=True)
    
    minimum_salary = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True, null=True)
    
    require_tailored_resume = models.BooleanField(default=True)
    
    allow_unknown_salary = models.BooleanField(default=False)
    allow_unknown_company = models.BooleanField(default=False)
    allow_external_ats = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AutoApply Config for {self.user.email} (Enabled: {self.auto_apply_enabled})"

class AutoApplyRun(models.Model):
    STATUS_CHOICES = (
        ('QUEUED', 'Queued'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('PARTIAL', 'Partial'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auto_apply_runs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUED', db_index=True)
    trigger = models.CharField(max_length=50, default='SCHEDULED')
    
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    jobs_discovered = models.IntegerField(default=0)
    jobs_evaluated = models.IntegerField(default=0)
    jobs_matched = models.IntegerField(default=0)
    applications_created = models.IntegerField(default=0)
    applications_prepared = models.IntegerField(default=0)
    applications_executed = models.IntegerField(default=0)
    applications_submitted = models.IntegerField(default=0)
    applications_user_action_required = models.IntegerField(default=0)
    applications_blocked = models.IntegerField(default=0)
    applications_failed = models.IntegerField(default=0)
    
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Run {self.id} for {self.user.email} ({self.status})"

class AutoApplyRunItem(models.Model):
    run = models.ForeignKey(AutoApplyRun, on_delete=models.CASCADE, related_name='items')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True, blank=True)
    
    stage = models.CharField(max_length=50) # MATCHING, POLICY_CHECK, PREPARATION, EXECUTION
    decision = models.CharField(max_length=50)
    reason_code = models.CharField(max_length=100, blank=True, null=True)
    
    execution_mode = models.CharField(max_length=50, blank=True, null=True)
    provider = models.CharField(max_length=100, blank=True, null=True)
    attempt_count = models.IntegerField(default=0)
    error_code = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Item {self.id} (Run {self.run.id}) - {self.decision}"

class UserActionRequired(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='action_required')
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    reason = models.CharField(max_length=100) # CAPTCHA, OTP, LOGIN, CONSENT, UNSUPPORTED_PROVIDER
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Action Required: {self.reason} for App {self.application.id}"
