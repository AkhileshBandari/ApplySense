from django.test import TestCase
from django.contrib.auth import get_user_model
from profiles.models import Profile, Skill, VerificationStatus
from jobs.models import Job, JobRequirement
from learning.models import (
    SkillTaxonomy, SkillAlias, SkillGapAnalysis, GapType, PriorityBand,
    LearningRoadmap, ProjectRecommendation, TargetType
)
from learning.services.taxonomy import SkillRequirementNormalizationService
from learning.services.gap_analysis import SkillGapAnalysisService, SkillGapPriorityService
from learning.services.roadmap import LearningRoadmapService

User = get_user_model()

class Phase7BIntelligenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")
        self.profile = Profile.objects.create(user=self.user)
        
        # Create taxonomy
        self.tax_python = SkillTaxonomy.objects.create(canonical_name="Python", slug="python")
        SkillAlias.objects.create(taxonomy=self.tax_python, alias_name="python3")
        
        # Add verified skill
        Skill.objects.create(profile=self.profile, name="python3", verification_status=VerificationStatus.VERIFIED)
        
        # Add unverified skill (should be ignored)
        Skill.objects.create(profile=self.profile, name="Docker", verification_status=VerificationStatus.UNVERIFIED)
        
        # Create a Job
        self.job = Job.objects.create(title="Backend Engineer", status='ACTIVE')
        self.req = JobRequirement.objects.create(
            job=self.job,
            required_skills=["Python", "Docker", "Kubernetes"],
            preferred_skills=["AWS"]
        )

    def test_alias_normalization(self):
        normalized = SkillRequirementNormalizationService.normalize_skill("python3")
        self.assertEqual(normalized, "Python")

    def test_verified_context_boundary(self):
        analysis = SkillGapAnalysisService.generate_analysis_for_job(self.user, self.job.id)
        
        # Python should be NO_GAP (it was python3 verified)
        python_gap = analysis.gap_items.get(canonical_skill="Python")
        self.assertIn(python_gap.gap_type, [GapType.NO_GAP, GapType.EVIDENCE_GAP])
        
        # Docker should be MISSING_SKILL because the profile's Docker is UNVERIFIED
        docker_gap = analysis.gap_items.get(canonical_skill="Docker")
        self.assertEqual(docker_gap.gap_type, GapType.MISSING_SKILL)

    def test_deterministic_priority(self):
        analysis = SkillGapAnalysisService.generate_analysis_for_job(self.user, self.job.id)
        docker_gap = analysis.gap_items.get(canonical_skill="Docker")
        # Required missing skill should be HIGH or CRITICAL depending on market freq
        self.assertIn(docker_gap.priority_band, [PriorityBand.HIGH, PriorityBand.CRITICAL])
        
        aws_gap = analysis.gap_items.get(canonical_skill="Aws")
        # Preferred missing skill should be LOW or MEDIUM
        self.assertIn(aws_gap.priority_band, [PriorityBand.LOW, PriorityBand.MEDIUM])

    def test_roadmap_creation(self):
        analysis = SkillGapAnalysisService.generate_analysis_for_job(self.user, self.job.id)
        roadmap = LearningRoadmapService.generate_roadmap(analysis, 10)
        
        self.assertEqual(roadmap.items.count(), 4) # Docker, Kubernetes, Aws, Python
        # Check ordering: Docker, K8s (REQUIRED) > Aws (PREFERRED)
        items = list(roadmap.items.all().order_by('sequence'))
        self.assertIn(items[0].canonical_skill, ["Docker", "Kubernetes", "Python"])
