from django.test import TestCase
from django.contrib.auth import get_user_model
from profiles.models import Profile, Experience, VerificationStatus
from profiles.services.candidate_context import CandidateContextService
from profiles.services.merge_service import MergeService

User = get_user_model()

class ProfileServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")
        self.profile = Profile.objects.create(user=self.user, name="Test User")
        
        self.verified_exp = Experience.objects.create(
            profile=self.profile,
            company="Verified Co",
            verification_status=VerificationStatus.VERIFIED
        )
        self.unverified_exp = Experience.objects.create(
            profile=self.profile,
            company="Unverified Co",
            verification_status=VerificationStatus.UNVERIFIED
        )

    def test_candidate_context_service_filters_unverified(self):
        context = CandidateContextService.get_for_user(self.user)
        
        exp_companies = [exp["company"] for exp in context["experience"]]
        self.assertIn("Verified Co", exp_companies)
        self.assertNotIn("Unverified Co", exp_companies)

    def test_merge_service_accept(self):
        success, obj = MergeService.accept_fact(self.user, Experience, self.unverified_exp.id)
        self.assertTrue(success)
        self.unverified_exp.refresh_from_db()
        self.assertEqual(self.unverified_exp.verification_status, VerificationStatus.VERIFIED)

    def test_merge_service_reject(self):
        success, obj = MergeService.reject_fact(self.user, Experience, self.unverified_exp.id)
        self.assertTrue(success)
        self.unverified_exp.refresh_from_db()
        self.assertEqual(self.unverified_exp.verification_status, VerificationStatus.REJECTED)
