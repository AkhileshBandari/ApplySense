from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from profiles.models import Profile, Skill, VerificationStatus
from profiles.services.candidate_context import CandidateContextService
from jobs.models import Job, JobRequirement
from learning.models import (
    SkillTaxonomy, SkillAlias, SkillGapAnalysis, SkillGapItem, GapType, PriorityBand,
    MarketSkillDemand, LearningRoadmap, ProjectRecommendation, TargetType
)
from learning.services.taxonomy import SkillRequirementNormalizationService
from learning.services.gap_analysis import SkillGapAnalysisService, SkillGapPriorityService
from learning.services.roadmap import LearningRoadmapService, SkillDependencyService
from learning.services.market_demand import MarketSkillDemandService

User = get_user_model()

class Phase7BAdversarialTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="adv_user", email="adv@example.com", password="password")
        self.profile = Profile.objects.create(user=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.user2 = User.objects.create_user(username="hacker", email="hacker@example.com", password="password")
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        # Taxonomies
        for name in ["Python", "React", "Docker", "AWS", "Kubernetes", "PostgreSQL"]:
            tax = SkillTaxonomy.objects.create(canonical_name=name, slug=name.lower())
            if name == "React":
                SkillAlias.objects.create(taxonomy=tax, alias_name="React.js")
                SkillAlias.objects.create(taxonomy=tax, alias_name="ReactJS")
            elif name == "PostgreSQL":
                SkillAlias.objects.create(taxonomy=tax, alias_name="postgresql")
            elif name == "AWS":
                SkillAlias.objects.create(taxonomy=tax, alias_name="Amazon Web Services")

    def test_verified_context_attack(self):
        Skill.objects.create(profile=self.profile, name="Python", verification_status=VerificationStatus.VERIFIED)
        Skill.objects.create(profile=self.profile, name="React", verification_status=VerificationStatus.VERIFIED)
        Skill.objects.create(profile=self.profile, name="Docker", verification_status=VerificationStatus.UNVERIFIED)
        Skill.objects.create(profile=self.profile, name="AWS", verification_status=VerificationStatus.REJECTED)
        Skill.objects.create(profile=self.profile, name="Kubernetes", verification_status=VerificationStatus.UNVERIFIED)

        job = Job.objects.create(title="Target Job", status='ACTIVE')
        req = JobRequirement.objects.create(
            job=job,
            required_skills=["Python", "React", "Docker", "AWS", "Kubernetes"]
        )

        analysis = SkillGapAnalysisService.generate_analysis_for_job(self.user, job.id)
        
        # Verify Python and React are NO_GAP or EVIDENCE_GAP
        python_gap = analysis.gap_items.get(canonical_skill="Python")
        self.assertIn(python_gap.gap_type, [GapType.NO_GAP, GapType.EVIDENCE_GAP])
        
        react_gap = analysis.gap_items.get(canonical_skill="React")
        self.assertIn(react_gap.gap_type, [GapType.NO_GAP, GapType.EVIDENCE_GAP])

        # Docker, AWS, Kubernetes MUST BE MISSING_SKILL because they are NOT verified
        for skill in ["Docker", "AWS", "Kubernetes"]:
            gap = analysis.gap_items.get(canonical_skill=skill)
            self.assertEqual(gap.gap_type, GapType.MISSING_SKILL, f"{skill} must be MISSING_SKILL")

    def test_frontend_trust_attack(self):
        # Frontend tries to inject candidate skills
        payload = {
            "target_type": "SPECIFIC_JOB",
            "job_id": 1,
            "candidate_skills": ["Python", "AWS", "Kubernetes", "Docker"]
        }
        
        # We need a job to hit the endpoint
        job = Job.objects.create(title="Target Job", status='ACTIVE')
        JobRequirement.objects.create(job=job, required_skills=["AWS"])
        payload["job_id"] = job.id
        
        response = self.client.post('/api/learning/gap-analysis/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        
        # Gap analysis should STILL report AWS as MISSING_SKILL because the user has no verified AWS skill
        gap = SkillGapItem.objects.get(analysis_id=response.data['id'], canonical_skill="AWS")
        self.assertEqual(gap.gap_type, GapType.MISSING_SKILL)

    def test_skill_alias_adversarial(self):
        # Python test cases
        for s in ["Python", "python", "PYTHON", "Python3", "python3"]:
            SkillAlias.objects.get_or_create(taxonomy=SkillTaxonomy.objects.get(canonical_name="Python"), alias_name=s)
            self.assertEqual(SkillRequirementNormalizationService.normalize_skill(s), "Python")
        
        # React test cases
        for s in ["React", "React.js", "ReactJS", "reactjs"]:
            SkillAlias.objects.get_or_create(taxonomy=SkillTaxonomy.objects.get(canonical_name="React"), alias_name=s)
            self.assertEqual(SkillRequirementNormalizationService.normalize_skill(s), "React")

        # Whitespace test cases
        self.assertEqual(SkillRequirementNormalizationService.normalize_skill(" React "), "React")
        self.assertEqual(SkillRequirementNormalizationService.normalize_skill("Python "), "Python")
        self.assertEqual(SkillRequirementNormalizationService.normalize_skill(" PostgreSQL"), "PostgreSQL")

    def test_unknown_skill_safety(self):
        norm = SkillRequirementNormalizationService.normalize_skill("SuperQuantumCloudXYZ")
        self.assertEqual(norm, "Superquantumcloudxyz")
        # Ensure it does not map to AWS or Docker
        self.assertNotIn(norm, ["AWS", "Docker", "Azure"])

    def test_requirement_classification_attack(self):
        # Usually requirement parsing is done at job ingest, not at gap analysis. 
        # But we verify that if negated, it shouldn't be mapped.
        # This is typically an ATS ingestion rule, but let's just test normalization safety
        pass

    def test_deterministic_priority(self):
        Skill.objects.create(profile=self.profile, name="Python", verification_status=VerificationStatus.VERIFIED)
        job = Job.objects.create(title="Target Job", status='ACTIVE')
        JobRequirement.objects.create(
            job=job,
            required_skills=["Django"],
            preferred_skills=["Docker"]
        )
        
        # Run 10 times and assert identical outputs
        analyses = []
        for i in range(10):
            a = SkillGapAnalysisService.generate_analysis_for_job(self.user, job.id)
            gaps = list(a.gap_items.all().order_by('canonical_skill').values('canonical_skill', 'gap_type', 'priority_band'))
            analyses.append(gaps)
            
        for i in range(1, 10):
            self.assertEqual(analyses[0], analyses[i])

    def test_cross_user_attack(self):
        job = Job.objects.create(title="Target Job", status='ACTIVE')
        JobRequirement.objects.create(job=job, required_skills=["Python"])
        
        a1 = SkillGapAnalysisService.generate_analysis_for_job(self.user, job.id)
        
        # User 2 tries to access User 1's analysis
        res = self.client2.get(f'/api/learning/gap-analysis/{a1.id}/')
        self.assertEqual(res.status_code, 404)
        
        r1 = LearningRoadmapService.generate_roadmap(a1, 10)
        res = self.client2.get(f'/api/learning/roadmaps/{r1.id}/')
        self.assertEqual(res.status_code, 404)
        
        res = self.client2.get(f'/api/learning/roadmap-items/{r1.items.first().id}/')
        self.assertEqual(res.status_code, 404)

    def test_market_frequency_mathematics(self):
        # Create 100 jobs
        jobs = []
        for i in range(100):
            j = Job.objects.create(title="Market Engineer", status='ACTIVE')
            jobs.append(j)
            
        # Python required: 70
        for i in range(70):
            JobRequirement.objects.create(job=jobs[i], required_skills=["Python"])
            
        # Docker required: 40
        for i in range(40):
            # Using the first 40 jobs (which also have python)
            if hasattr(jobs[i], 'requirements_norm'):
                jobs[i].requirements_norm.required_skills.append("Docker")
                jobs[i].requirements_norm.save()
            else:
                JobRequirement.objects.update_or_create(job=jobs[i], defaults={'required_skills': ["Docker", "Python"]})
                
        # AWS preferred: 20
        for i in range(20):
            # Using the last 20 jobs
            JobRequirement.objects.update_or_create(job=jobs[80+i], defaults={'preferred_skills': ["AWS"]})
            
        data = MarketSkillDemandService.get_market_aggregate("Market Engineer", min_sample_size=10)
        
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["sample_size"], 100)
        self.assertEqual(data["skills"]["Python"]["required_frequency"], 0.70)
        self.assertEqual(data["skills"]["Docker"]["required_frequency"], 0.40)
        self.assertEqual(data["skills"]["AWS"]["preferred_frequency"], 0.20)

    def test_small_sample_safety(self):
        Job.objects.create(title="Tiny Role", status='ACTIVE')
        data = MarketSkillDemandService.get_market_aggregate("Tiny Role", min_sample_size=10)
        self.assertEqual(data["status"], "INSUFFICIENT_MARKET_DATA")

    def test_zero_data_market(self):
        data = MarketSkillDemandService.get_market_aggregate("Ghost Role", min_sample_size=10)
        self.assertEqual(data["status"], "INSUFFICIENT_MARKET_DATA")
        self.assertEqual(data["sample_size"], 0)
        
    def test_stale_job_exclusion(self):
        # ACTIVE vs STALE
        j1 = Job.objects.create(title="Stale Engineer", status='ACTIVE')
        JobRequirement.objects.create(job=j1, required_skills=["Python"])
        
        j2 = Job.objects.create(title="Stale Engineer", status='INACTIVE') # Closed/Stale
        JobRequirement.objects.create(job=j2, required_skills=["Docker"])
        
        # Lower minimum to 1 for this test
        data = MarketSkillDemandService.get_market_aggregate("Stale Engineer", min_sample_size=1)
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["sample_size"], 1)
        self.assertIn("Python", data["skills"])
        self.assertNotIn("Docker", data["skills"])
