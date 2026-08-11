from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class CareerDecisionPlanVersion(models.fields.related.ForeignKey):
    pass # forward decl for type hints

class CareerDecisionPlanVersion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_decision_plans')
    generated_at = models.DateTimeField(default=timezone.now)
    input_snapshot_hash = models.CharField(max_length=255, help_text="Hash to detect staleness")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-generated_at']

class CareerDecisionSnapshot(models.Model):
    plan_version = models.OneToOneField(CareerDecisionPlanVersion, on_delete=models.CASCADE, related_name='snapshot')
    data = models.JSONField(help_text="Immutable snapshot of the inputs used (skills, readiness, market, pathways).")

class PriorityCategory(models.TextChoices):
    SKILL_GAP = 'SKILL_GAP', 'Skill Gap'
    EVIDENCE_GAP = 'EVIDENCE_GAP', 'Evidence Gap'
    INTERVIEW_GAP = 'INTERVIEW_GAP', 'Interview Gap'
    CAREER_BRAND_GAP = 'CAREER_BRAND_GAP', 'Career Brand Gap'
    APPLICATION_STRATEGY = 'APPLICATION_STRATEGY', 'Application Strategy'
    JOB_MARKET_ALIGNMENT = 'JOB_MARKET_ALIGNMENT', 'Job Market Alignment'
    WORK_AUTHORIZATION = 'WORK_AUTHORIZATION', 'Work Authorization'
    SPONSORSHIP = 'SPONSORSHIP', 'Sponsorship'
    COMPENSATION_ALIGNMENT = 'COMPENSATION_ALIGNMENT', 'Compensation Alignment'
    APPLICATION_CONVERSION = 'APPLICATION_CONVERSION', 'Application Conversion'
    TARGET_ROLE_MISMATCH = 'TARGET_ROLE_MISMATCH', 'Target Role Mismatch'

class CareerPriority(models.Model):
    plan_version = models.ForeignKey(CareerDecisionPlanVersion, on_delete=models.CASCADE, related_name='priorities')
    category = models.CharField(max_length=50, choices=PriorityCategory.choices)
    severity = models.CharField(max_length=20) # e.g. HIGH, MEDIUM, LOW
    impact_score = models.IntegerField(help_text="Deterministic 0-100 score")
    urgency = models.IntegerField(help_text="0-100 scale")
    confidence = models.IntegerField(help_text="0-100 scale based on data volume")
    explanation = models.TextField()
    evidence_references = models.JSONField(default=list)
    recommended_action = models.CharField(max_length=255)
    
    class Meta:
        ordering = ['-impact_score']

class ActionType(models.TextChoices):
    INFORMATIONAL = 'INFORMATIONAL', 'Informational'
    USER_ACTION_REQUIRED = 'USER_ACTION_REQUIRED', 'User Action Required'
    PREPARE = 'PREPARE', 'Prepare'
    REVIEW_REQUIRED = 'REVIEW_REQUIRED', 'Review Required'
    AUTO_EXECUTABLE = 'AUTO_EXECUTABLE', 'Auto Executable'
    BLOCKED = 'BLOCKED', 'Blocked'

class ActionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    EXPIRED = 'EXPIRED', 'Expired'
    FAILED = 'FAILED', 'Failed'

class CareerAction(models.Model):
    plan_version = models.ForeignKey(CareerDecisionPlanVersion, on_delete=models.CASCADE, related_name='actions')
    title = models.CharField(max_length=255)
    description = models.TextField()
    action_type = models.CharField(max_length=50, choices=ActionType.choices)
    status = models.CharField(max_length=50, choices=ActionStatus.choices, default=ActionStatus.PENDING)
    source_phase = models.CharField(max_length=50) # e.g. PHASE_7B
    
    impact_score = models.IntegerField(default=0)
    urgency_score = models.IntegerField(default=0)
    effort_penalty = models.IntegerField(default=0)
    final_score = models.IntegerField(default=0) # Ranked by this
    
    reason = models.TextField()
    evidence_references = models.JSONField(default=list)
    target_role = models.CharField(max_length=100, blank=True)
    target_country = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class CareerActionDependency(models.Model):
    action = models.ForeignKey(CareerAction, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(CareerAction, on_delete=models.CASCADE, related_name='dependent_actions')
    
    class Meta:
        unique_together = ('action', 'depends_on')
