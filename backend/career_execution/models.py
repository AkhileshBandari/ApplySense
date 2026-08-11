from django.db import models
from django.conf import settings
from career_decisions.models import CareerAction

class ExecutionMode(models.TextChoices):
    USER_ACTION = 'USER_ACTION', 'User Action'
    ASSISTED = 'ASSISTED', 'Assisted'
    REVIEW_REQUIRED = 'REVIEW_REQUIRED', 'Review Required'
    AUTO_EXECUTABLE = 'AUTO_EXECUTABLE', 'Auto Executable'
    SYSTEM_OBSERVATION = 'SYSTEM_OBSERVATION', 'System Observation'
    BLOCKED = 'BLOCKED', 'Blocked'

class ExecutionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    READY = 'READY', 'Ready'
    BLOCKED = 'BLOCKED', 'Blocked'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    WAITING_FOR_USER = 'WAITING_FOR_USER', 'Waiting For User'
    WAITING_FOR_SYSTEM = 'WAITING_FOR_SYSTEM', 'Waiting For System'
    REVIEW_REQUIRED = 'REVIEW_REQUIRED', 'Review Required'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    EXPIRED = 'EXPIRED', 'Expired'
    SUPERSEDED = 'SUPERSEDED', 'Superseded'

class CareerExecutionPlan(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='career_execution_plan')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CareerExecutionItem(models.Model):
    plan = models.ForeignKey(CareerExecutionPlan, on_delete=models.CASCADE, related_name='items')
    
    # Identifiers
    title = models.CharField(max_length=255)
    description = models.TextField()
    action_type = models.CharField(max_length=50)
    source_phase = models.CharField(max_length=50)
    
    # State
    status = models.CharField(max_length=50, choices=ExecutionStatus.choices, default=ExecutionStatus.PENDING)
    execution_mode = models.CharField(max_length=50, choices=ExecutionMode.choices, default=ExecutionMode.USER_ACTION)
    
    # Ranking
    impact_score = models.IntegerField(default=0)
    urgency_score = models.IntegerField(default=0)
    effort_penalty = models.IntegerField(default=0)
    final_score = models.IntegerField(default=0)
    
    # The action that generated this item. Note: This can become null if the item is reconciled without an active source action
    source_action = models.ForeignKey(CareerAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='execution_items')
    
    reason = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class CareerExecutionDependency(models.Model):
    item = models.ForeignKey(CareerExecutionItem, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(CareerExecutionItem, on_delete=models.CASCADE, related_name='dependent_items')
    
    class Meta:
        unique_together = ('item', 'depends_on')

class CareerExecutionProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='execution_progress_history')
    overall_score = models.IntegerField(default=0)
    skill_score = models.IntegerField(default=0)
    evidence_score = models.IntegerField(default=0)
    brand_score = models.IntegerField(default=0)
    interview_score = models.IntegerField(default=0)
    application_score = models.IntegerField(default=0)
    pathway_score = models.IntegerField(default=0)
    
    timestamp = models.DateTimeField(auto_now_add=True)

class OutcomeType(models.TextChoices):
    SUCCESS = 'SUCCESS', 'Success'
    PARTIAL_SUCCESS = 'PARTIAL_SUCCESS', 'Partial Success'
    USER_COMPLETED = 'USER_COMPLETED', 'User Completed'
    SYSTEM_COMPLETED = 'SYSTEM_COMPLETED', 'System Completed'
    BLOCKED = 'BLOCKED', 'Blocked'
    FAILED = 'FAILED', 'Failed'
    UNKNOWN = 'UNKNOWN', 'Unknown'
    SUPERSEDED = 'SUPERSEDED', 'Superseded'

class CareerExecutionOutcome(models.Model):
    item = models.OneToOneField(CareerExecutionItem, on_delete=models.CASCADE, related_name='outcome')
    outcome_type = models.CharField(max_length=50, choices=OutcomeType.choices)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

class CareerExecutionEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='execution_events')
    event_type = models.CharField(max_length=50)
    item = models.ForeignKey(CareerExecutionItem, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
