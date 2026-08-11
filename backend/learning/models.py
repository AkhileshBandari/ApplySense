from django.db import models
from django.conf import settings

# ----------------------------------------------------------------------
# Taxonomy & Normalization
# ----------------------------------------------------------------------

class SkillTaxonomy(models.Model):
    canonical_name = models.CharField(max_length=150, unique=True, db_index=True)
    slug = models.SlugField(max_length=150, unique=True)
    category = models.CharField(max_length=100, blank=True)
    subcategory = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Skill Taxonomies"

    def __str__(self):
        return self.canonical_name

class SkillAlias(models.Model):
    taxonomy = models.ForeignKey(SkillTaxonomy, on_delete=models.CASCADE, related_name='aliases')
    alias_name = models.CharField(max_length=150, unique=True, db_index=True)
    
    class Meta:
        verbose_name_plural = "Skill Aliases"

    def __str__(self):
        return f"{self.alias_name} -> {self.taxonomy.canonical_name}"

# ----------------------------------------------------------------------
# Target Abstraction
# ----------------------------------------------------------------------

class TargetType(models.TextChoices):
    SPECIFIC_JOB = 'SPECIFIC_JOB', 'Specific Job'
    TARGET_ROLE = 'TARGET_ROLE', 'Target Role'
    MARKET_AGGREGATE = 'MARKET_AGGREGATE', 'Market Aggregate'

# ----------------------------------------------------------------------
# Skill Gap Analysis
# ----------------------------------------------------------------------

class SkillGapAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gap_analyses')
    target_type = models.CharField(max_length=50, choices=TargetType.choices)
    
    # Specific Job target
    target_job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True, related_name='gap_analyses')
    
    # Role / Market targets
    target_role = models.CharField(max_length=150, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    region = models.CharField(max_length=150, blank=True)
    experience_level = models.CharField(max_length=50, blank=True)
    work_mode = models.CharField(max_length=50, blank=True)
    
    # Context snapshots to keep analysis immutable historically
    candidate_context_snapshot = models.JSONField(default=dict)
    requirement_snapshot = models.JSONField(default=dict)
    
    market_sample_size = models.IntegerField(default=0)
    analysis_version = models.CharField(max_length=20, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Skill Gap Analyses"

    def __str__(self):
        return f"Gap Analysis for {self.user.email} - {self.target_type}"

class GapType(models.TextChoices):
    NO_GAP = 'NO_GAP', 'No Gap'
    PROFICIENCY_GAP = 'PROFICIENCY_GAP', 'Proficiency Gap'
    EXPERIENCE_GAP = 'EXPERIENCE_GAP', 'Experience Gap'
    MISSING_SKILL = 'MISSING_SKILL', 'Missing Skill'
    EVIDENCE_GAP = 'EVIDENCE_GAP', 'Evidence Gap'

class PriorityBand(models.TextChoices):
    CRITICAL = 'CRITICAL', 'Critical'
    HIGH = 'HIGH', 'High'
    MEDIUM = 'MEDIUM', 'Medium'
    LOW = 'LOW', 'Low'

class SkillGapItem(models.Model):
    analysis = models.ForeignKey(SkillGapAnalysis, on_delete=models.CASCADE, related_name='gap_items')
    canonical_skill = models.CharField(max_length=150)
    
    candidate_state = models.CharField(max_length=50) # e.g. VERIFIED_PRESENT, VERIFIED_PARTIAL, NOT_VERIFIED
    requirement_state = models.CharField(max_length=50) # e.g. REQUIRED, PREFERRED, OPTIONAL
    gap_type = models.CharField(max_length=50, choices=GapType.choices)
    
    priority_score = models.FloatField(default=0.0)
    priority_band = models.CharField(max_length=50, choices=PriorityBand.choices, default=PriorityBand.LOW)
    
    reason = models.TextField(blank=True)
    evidence = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.canonical_skill} ({self.gap_type})"

# ----------------------------------------------------------------------
# Market Demand Cache (Optional optimization)
# ----------------------------------------------------------------------

class MarketSkillDemand(models.Model):
    target_role = models.CharField(max_length=150)
    country_code = models.CharField(max_length=10, blank=True)
    experience_level = models.CharField(max_length=50, blank=True)
    
    canonical_skill = models.CharField(max_length=150)
    sample_size = models.IntegerField(default=0)
    required_frequency = models.FloatField(default=0.0)
    preferred_frequency = models.FloatField(default=0.0)
    
    last_computed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('target_role', 'country_code', 'experience_level', 'canonical_skill')

# ----------------------------------------------------------------------
# Learning Roadmap
# ----------------------------------------------------------------------

class LearningRoadmap(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roadmaps')
    analysis = models.ForeignKey(SkillGapAnalysis, on_delete=models.CASCADE, related_name='roadmaps')
    
    title = models.CharField(max_length=255)
    hours_per_week = models.IntegerField(default=10)
    target_completion_date = models.DateField(null=True, blank=True)
    
    is_stale = models.BooleanField(default=False)
    stale_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Roadmap for {self.user.email}"

class RoadmapItemStatus(models.TextChoices):
    NOT_STARTED = 'NOT_STARTED', 'Not Started'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    BLOCKED = 'BLOCKED', 'Blocked'
    SKIPPED = 'SKIPPED', 'Skipped'

class LearningRoadmapItem(models.Model):
    roadmap = models.ForeignKey(LearningRoadmap, on_delete=models.CASCADE, related_name='items')
    canonical_skill = models.CharField(max_length=150)
    
    title = models.CharField(max_length=255)
    objective = models.TextField()
    priority = models.CharField(max_length=50, choices=PriorityBand.choices)
    sequence = models.IntegerField(default=1)
    
    estimated_effort_hours = models.FloatField(null=True, blank=True)
    dependency_skills = models.JSONField(default=list) # List of canonical_skill strings
    completion_criteria = models.TextField(blank=True)
    
    status = models.CharField(max_length=50, choices=RoadmapItemStatus.choices, default=RoadmapItemStatus.NOT_STARTED)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.sequence}. {self.canonical_skill}"

# ----------------------------------------------------------------------
# Learning Resources
# ----------------------------------------------------------------------

class ResourceType(models.TextChoices):
    DOCUMENTATION = 'DOCUMENTATION', 'Documentation'
    COURSE = 'COURSE', 'Course'
    VIDEO = 'VIDEO', 'Video'
    BOOK = 'BOOK', 'Book'
    PRACTICE = 'PRACTICE', 'Practice'
    CERTIFICATION = 'CERTIFICATION', 'Certification'
    LAB = 'LAB', 'Lab'

class CostType(models.TextChoices):
    FREE = 'FREE', 'Free'
    PAID = 'PAID', 'Paid'
    FREEMIUM = 'FREEMIUM', 'Freemium'
    UNKNOWN = 'UNKNOWN', 'Unknown'

class LearningResource(models.Model):
    canonical_skill = models.CharField(max_length=150, db_index=True)
    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=150)
    resource_type = models.CharField(max_length=50, choices=ResourceType.choices)
    url = models.URLField(max_length=500)
    
    difficulty = models.CharField(max_length=50, blank=True)
    estimated_duration_hours = models.FloatField(null=True, blank=True)
    cost_type = models.CharField(max_length=50, choices=CostType.choices, default=CostType.UNKNOWN)
    
    country_availability = models.JSONField(default=list) # List of country codes, empty means global
    verification_status = models.CharField(max_length=50, default='VERIFIED')
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

# ----------------------------------------------------------------------
# Project Recommendations
# ----------------------------------------------------------------------

class ProjectStatus(models.TextChoices):
    RECOMMENDED = 'RECOMMENDED', 'Recommended'
    PLANNED = 'PLANNED', 'Planned'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    ARCHIVED = 'ARCHIVED', 'Archived'

class ProjectRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_recommendations')
    analysis = models.ForeignKey(SkillGapAnalysis, on_delete=models.CASCADE, related_name='project_recommendations')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    difficulty = models.CharField(max_length=50, blank=True)
    
    target_skills = models.JSONField(default=list) # Missing skills this project helps close
    priority = models.CharField(max_length=50, choices=PriorityBand.choices, default=PriorityBand.MEDIUM)
    
    estimated_effort_hours = models.FloatField(null=True, blank=True)
    deliverables = models.JSONField(default=list)
    success_criteria = models.JSONField(default=list)
    
    status = models.CharField(max_length=50, choices=ProjectStatus.choices, default=ProjectStatus.RECOMMENDED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Project: {self.title} for {self.user.email}"
