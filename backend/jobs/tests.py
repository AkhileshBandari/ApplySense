from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Job, JobRequirement, JobMatch, SavedJob
from .services.ingestion import JobValidationService, JobDeduplicationService, SkillNormalizationService
from .services.hybrid_matcher import HybridMatcherService

class JobIngestionTests(TestCase):
    def test_validation_rejects_invalid_jobs(self):
        # Missing title
        self.assertFalse(JobValidationService.validate({"company": "Acme", "description": "Long enough description here..." * 5}))
        # Description too short
        self.assertFalse(JobValidationService.validate({"title": "Dev", "company": "Acme", "description": "Short"}))
        # Valid
        self.assertTrue(JobValidationService.validate({"title": "Dev", "company": "Acme", "description": "A very long description that easily bypasses the minimum length threshold imposed by the validator."}))

    def test_skill_normalization(self):
        self.assertEqual(SkillNormalizationService.normalize("React.js"), "React")
        self.assertEqual(SkillNormalizationService.normalize("AWS"), "AWS")
        self.assertEqual(SkillNormalizationService.normalize(" amazon web services "), "AWS")
        self.assertEqual(SkillNormalizationService.normalize("unknown_skill"), "Unknown_Skill")

    def test_deduplication(self):
        Job.objects.create(title="Engineer", company="Acme", source_job_id="123", source_url="http://acme.com/123", location="Remote")
        
        # Match by URL
        dup1 = JobDeduplicationService.find_exact_duplicate("http://acme.com/123", "", "", "", "")
        self.assertIsNotNone(dup1)
        
        # Match by source ID
        dup2 = JobDeduplicationService.find_exact_duplicate("", "123", "Acme", "", "")
        self.assertIsNotNone(dup2)
        
        # Match heuristic fallback
        dup3 = JobDeduplicationService.find_exact_duplicate("", "", "Acme", "Engineer", "Remote")
        self.assertIsNotNone(dup3)
        
        # No match
        none_dup = JobDeduplicationService.find_exact_duplicate("", "456", "Beta", "Engineer", "Remote")
        self.assertIsNone(none_dup)


class HybridMatcherTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.job = Job.objects.create(title="Python Dev", company="Acme", description="Need python")
        self.req = JobRequirement.objects.create(
            job=self.job,
            required_skills=["Python", "Django"],
            preferred_skills=["Docker"],
            minimum_experience=3
        )
        
    def test_match_perfect_candidate(self):
        context = {
            "skills": ["Python", "Django", "Docker", "AWS"],
            "experiences": [{"years": 4}]
        }
        
        skills_score, skills_det = HybridMatcherService._match_skills(context, self.job)
        self.assertEqual(skills_score, 100)
        self.assertEqual(len(skills_det["missing_required"]), 0)
        
        exp_score, _ = HybridMatcherService._match_experience(context, self.job)
        self.assertEqual(exp_score, 100)

    def test_match_missing_required(self):
        context = {
            "skills": ["Python"], # Missing Django
            "experiences": [{"years": 3}]
        }
        
        skills_score, skills_det = HybridMatcherService._match_skills(context, self.job)
        self.assertLess(skills_score, 100)
        self.assertIn("django", skills_det["missing_required"])

    def test_match_fresher(self):
        context = {
            "skills": ["Python", "Django"],
            "experiences": [{"years": 0}]
        }
        
        exp_score, _ = HybridMatcherService._match_experience(context, self.job)
        self.assertEqual(exp_score, 25) # Misses 3 year requirement
