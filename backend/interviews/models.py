from django.db import models
from django.conf import settings

class InterviewPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_plans')
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True)
    application = models.ForeignKey('applications.Application', on_delete=models.SET_NULL, null=True, blank=True)
    resume_version = models.ForeignKey('resumes.ResumeVersion', on_delete=models.SET_NULL, null=True, blank=True)
    target_role = models.CharField(max_length=255, blank=True, null=True)
    interview_type = models.CharField(max_length=50) # JOB_SPECIFIC, TECHNICAL, BEHAVIORAL, CODING, etc.
    difficulty = models.CharField(max_length=50, default='INTERMEDIATE')
    status = models.CharField(max_length=50, default='DRAFT')
    context_snapshot = models.JSONField(blank=True, null=True)
    plan_version = models.CharField(max_length=50, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class InterviewPlanSection(models.Model):
    plan = models.ForeignKey(InterviewPlan, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=50) # ROLE_OVERVIEW, TECHNICAL, BEHAVIORAL, SYSTEM_DESIGN, CODING, etc.
    priority = models.IntegerField(default=0)
    reason_code = models.CharField(max_length=100) # JOB_REQUIRED, CANDIDATE_GAP, etc.
    estimated_weight = models.FloatField(default=1.0)
    structured_content = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class MockInterviewSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mock_sessions')
    plan = models.ForeignKey(InterviewPlan, on_delete=models.CASCADE, related_name='sessions')
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True)
    application = models.ForeignKey('applications.Application', on_delete=models.SET_NULL, null=True, blank=True)
    mode = models.CharField(max_length=50, default='TEXT')
    difficulty = models.CharField(max_length=50, default='INTERMEDIATE')
    status = models.CharField(max_length=50, default='CREATED') # CREATED, READY, IN_PROGRESS, PAUSED, COMPLETED, ABANDONED, FAILED
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    context_snapshot = models.JSONField(blank=True, null=True)
    overall_readiness_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class InterviewQuestion(models.Model):
    session = models.ForeignKey(MockInterviewSession, on_delete=models.CASCADE, related_name='questions')
    plan = models.ForeignKey(InterviewPlan, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_type = models.CharField(max_length=50)
    category = models.CharField(max_length=50, blank=True, null=True)
    difficulty = models.CharField(max_length=50, default='INTERMEDIATE')
    question_text = models.TextField()
    reason_code = models.CharField(max_length=100, blank=True, null=True)
    source_refs = models.JSONField(blank=True, null=True)
    expected_concepts = models.JSONField(blank=True, null=True)
    sequence = models.IntegerField(default=0)
    parent_question = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='follow_ups')
    is_follow_up = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class InterviewResponse(models.Model):
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    response_text = models.TextField()
    response_source = models.CharField(max_length=50, default='TEXT')
    submitted_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.IntegerField(default=0)
    evaluation_status = models.CharField(max_length=50, default='PENDING') # PENDING, COMPLETED, FAILED
    created_at = models.DateTimeField(auto_now_add=True)

class InterviewResponseEvaluation(models.Model):
    response = models.OneToOneField(InterviewResponse, on_delete=models.CASCADE, related_name='evaluation')
    relevance_score = models.IntegerField(null=True, blank=True)
    completeness_score = models.IntegerField(null=True, blank=True)
    technical_accuracy_score = models.IntegerField(null=True, blank=True)
    structure_score = models.IntegerField(null=True, blank=True)
    evidence_score = models.IntegerField(null=True, blank=True)
    communication_score = models.IntegerField(null=True, blank=True)
    overall_score = models.IntegerField(null=True, blank=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    missing_concepts = models.JSONField(default=list)
    unsupported_claims = models.JSONField(default=list)
    feedback = models.TextField(blank=True, null=True)
    evaluation_version = models.CharField(max_length=50, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)

class InterviewWeakness(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_weaknesses')
    session = models.ForeignKey(MockInterviewSession, on_delete=models.CASCADE, related_name='weaknesses')
    category = models.CharField(max_length=100)
    skill = models.CharField(max_length=100, blank=True, null=True)
    severity = models.CharField(max_length=50) # LOW, MEDIUM, HIGH, CRITICAL
    reason_code = models.CharField(max_length=100, blank=True, null=True)
    evidence = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=50, default='IDENTIFIED')
    created_at = models.DateTimeField(auto_now_add=True)

class InterviewImprovementPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_improvement_plans')
    session = models.ForeignKey(MockInterviewSession, on_delete=models.CASCADE, related_name='improvement_plans')
    structured_content = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
