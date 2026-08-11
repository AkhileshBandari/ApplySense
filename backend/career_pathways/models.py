from django.db import models
from django.conf import settings

class CareerPath(models.Model):
    """Represents a potential career destination."""
    canonical_role_name = models.CharField(max_length=150, unique=True, db_index=True)
    target_role = models.CharField(max_length=150)
    role_family = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    
    target_country = models.CharField(max_length=10, blank=True)
    target_region = models.CharField(max_length=150, blank=True)
    work_mode = models.CharField(max_length=50, blank=True) # remote, hybrid, onsite
    employment_type = models.CharField(max_length=50, blank=True)
    
    source = models.CharField(max_length=150, blank=True) # e.g. system, market_aggregate
    active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.canonical_role_name


class CareerPathRequirement(models.Model):
    """Represents requirements associated with a career path."""
    path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name='requirements')
    canonical_skill = models.CharField(max_length=150, db_index=True)
    skill_category = models.CharField(max_length=100, blank=True)
    
    is_required = models.BooleanField(default=True) # True = REQUIRED, False = PREFERRED
    min_experience_months = models.IntegerField(default=0)
    
    market_demand_reference = models.CharField(max_length=255, blank=True)
    provenance = models.CharField(max_length=100, blank=True)
    requirement_source = models.CharField(max_length=150, blank=True)
    confidence_classification = models.CharField(max_length=50, blank=True) # HIGH, MEDIUM, LOW

    def __str__(self):
        return f"{self.path.canonical_role_name} requires {self.canonical_skill}"


class ScenarioStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    SIMULATED = 'SIMULATED', 'Simulated'
    ARCHIVED = 'ARCHIVED', 'Archived'

class CareerPathScenario(models.Model):
    """Represents a hypothetical simulation."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='career_scenarios')
    name = models.CharField(max_length=255)
    
    target_path = models.ForeignKey(CareerPath, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Optional manual overrides (if they want to simulate something outside a predefined path)
    target_role = models.CharField(max_length=150, blank=True)
    target_country = models.CharField(max_length=10, blank=True)
    target_region = models.CharField(max_length=150, blank=True)
    work_mode = models.CharField(max_length=50, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    
    # Immutable baseline snapshot representing CandidateContext at creation time
    baseline_snapshot = models.JSONField(default=dict)
    
    # The output of applying assumptions to the baseline
    simulated_snapshot = models.JSONField(default=dict)
    
    status = models.CharField(max_length=50, choices=ScenarioStatus.choices, default=ScenarioStatus.DRAFT)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Scenario: {self.name} for {self.user.email}"


class AssumptionType(models.TextChoices):
    SKILL = 'SKILL', 'Skill'
    LEARNING = 'LEARNING', 'Learning'
    EXPERIENCE = 'EXPERIENCE', 'Experience'
    EVIDENCE = 'EVIDENCE', 'Evidence'
    MARKET = 'MARKET', 'Market'
    LOCATION = 'LOCATION', 'Location'
    WORK_AUTHORIZATION = 'WORK_AUTHORIZATION', 'Work Authorization'
    INTERVIEW = 'INTERVIEW', 'Interview'
    CAREER_BRAND = 'CAREER_BRAND', 'Career Brand'

class ScenarioAssumption(models.Model):
    """Structured assumptions for a simulation scenario."""
    scenario = models.ForeignKey(CareerPathScenario, on_delete=models.CASCADE, related_name='assumptions')
    assumption_type = models.CharField(max_length=50, choices=AssumptionType.choices)
    
    # Structured representation of the assumption
    # e.g. {"skill": "Kubernetes", "level": "ADVANCED"}
    # e.g. {"country": "US", "sponsorship_required": False}
    structured_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.assumption_type} assumption for {self.scenario.name}"
