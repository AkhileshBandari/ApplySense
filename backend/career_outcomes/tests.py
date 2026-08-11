from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from career_outcomes.models import CareerOutcomeRecord, NormalizedOutcomeState
from career_outcomes.services.normalization_service import OutcomeNormalizationService
from career_outcomes.services.funnel_analysis_service import FunnelAnalysisService
from career_outcomes.services.attribution_service import AttributionAnalysisService
from career_outcomes.services.recommendation_engine import RecommendationEngineService

User = get_user_model()

class CareerOutcomesImplementationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@test.com", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_normalization_service(self):
        self.assertEqual(OutcomeNormalizationService.normalize("Interview"), NormalizedOutcomeState.INTERVIEW)
        self.assertEqual(OutcomeNormalizationService.normalize("Employer contacted you"), NormalizedOutcomeState.SCREENING)
        self.assertEqual(OutcomeNormalizationService.normalize("offer received"), NormalizedOutcomeState.OFFER)
        self.assertEqual(OutcomeNormalizationService.normalize("some random state"), NormalizedOutcomeState.UNKNOWN)
        self.assertEqual(OutcomeNormalizationService.normalize(None), NormalizedOutcomeState.UNKNOWN)

    def test_funnel_analysis_insufficient_sample(self):
        # 0 applications should trigger INSUFFICIENT_SAMPLE
        funnel = FunnelAnalysisService.calculate_funnel(self.user)
        self.assertEqual(funnel["status"], "INSUFFICIENT_SAMPLE")

    def test_funnel_analysis_safe_math(self):
        # Add 10 applications and 5 screens
        for i in range(15):
            state = NormalizedOutcomeState.APPLIED if i < 10 else NormalizedOutcomeState.SCREENING
            CareerOutcomeRecord.objects.create(user=self.user, normalized_state=state)
            
        funnel = FunnelAnalysisService.calculate_funnel(self.user)
        self.assertEqual(funnel["status"], "SUCCESS")
        self.assertEqual(funnel["total_apps"], 10)
        self.assertEqual(funnel["screening_rate"], 50.0)
        self.assertEqual(funnel["interview_rate"], 0.0)
        self.assertEqual(funnel["offer_rate"], 0.0)
        self.assertEqual(funnel["acceptance_rate"], 0.0) # Safe math handling zero denominators

    def test_attribution_insufficient_sample(self):
        for i in range(5):
            CareerOutcomeRecord.objects.create(user=self.user, normalized_state=NormalizedOutcomeState.APPLIED, resume_version_id=1)
        
        perf = AttributionAnalysisService.analyze_resume_performance(self.user)
        self.assertEqual(perf["resume_performance"][0]["status"], "INSUFFICIENT_COMPARABLE_SAMPLE")

    def test_attribution_success(self):
        for i in range(10):
            CareerOutcomeRecord.objects.create(user=self.user, normalized_state=NormalizedOutcomeState.APPLIED, resume_version_id=1)
        for i in range(2):
            CareerOutcomeRecord.objects.create(user=self.user, normalized_state=NormalizedOutcomeState.INTERVIEW, resume_version_id=1)
            
        perf = AttributionAnalysisService.analyze_resume_performance(self.user)
        rp = perf["resume_performance"][0]
        self.assertEqual(rp["status"], "OBSERVED_ASSOCIATION")
        self.assertEqual(rp["total_apps"], 10)
        # 2 interviews out of 10 total apps -> 20.0%
        self.assertAlmostEqual(rp["interview_rate"], 20.0)

    def test_recommendation_engine(self):
        # Set up a low response rate scenario (e.g. 20 apps, 0 screens)
        for _ in range(20):
            CareerOutcomeRecord.objects.create(user=self.user, normalized_state=NormalizedOutcomeState.APPLIED)
            
        recs = RecommendationEngineService.generate_recommendations(self.user)
        self.assertTrue(any(r["recommended_action"] == "Review targeting / resume alignment." for r in recs))
        # Ensure no causal claims
        self.assertFalse(recs[0]["causal_claim_allowed"])

    def test_api_read_only_protection(self):
        # Cannot POST to outcomes
        res = self.client.post('/api/career-outcomes/events/', {
            "normalized_state": "OFFER"
        })
        self.assertEqual(res.status_code, 405)

    def test_api_endpoints_success(self):
        res1 = self.client.get('/api/career-outcomes/events/funnel/')
        self.assertEqual(res1.status_code, 200)
        
        res2 = self.client.get('/api/career-outcomes/events/resume_performance/')
        self.assertEqual(res2.status_code, 200)

        res3 = self.client.get('/api/career-outcomes/events/match_performance/')
        self.assertEqual(res3.status_code, 200)
        
        res4 = self.client.get('/api/career-outcomes/events/recommendations/')
        self.assertEqual(res4.status_code, 200)
