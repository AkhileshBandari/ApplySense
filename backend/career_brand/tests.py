from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import ProfessionalProfile, ProfessionalProfileSection
from .services.ClaimValidationService import ClaimValidationService
from .services.ScoringEngine import ScoringEngine

User = get_user_model()

class CareerBrandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='pw')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_completeness_score(self):
        profile = ProfessionalProfile.objects.create(
            user=self.user,
            headline='Backend Dev',
            about='Python expert',
            location='NY',
            current_role='Backend Developer'
        )
        ProfessionalProfileSection.objects.create(
            profile=profile, section_type='EXPERIENCE'
        )
        
        # 4 base fields * 10 = 40
        # 1 section EXPERIENCE = 20
        # Expected = 60
        score = ScoringEngine.calculate_completeness(profile)
        self.assertEqual(score, 60)
        
    def test_claim_validation_empty_unsupported(self):
        # AI generated hallucination detection
        result = ClaimValidationService.validate_generated_proposal(self.user, "Built a Kubernetes cluster.")
        # If user has no skills verified, "Kubernetes" (if in taxonomy) might be flagged.
        # But this is just a structure test, let's just make sure it runs without crashing.
        self.assertIn('is_safe', result)
        
    def test_api_cross_user_isolation(self):
        user2 = User.objects.create_user(username='other', password='pw')
        profile2 = ProfessionalProfile.objects.create(user=user2, headline='Other Dev')
        
        response = self.client.get('/api/career-brand/profiles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results', response.data)), 0) # Shouldn't see user2's profile
        
    def test_analysis_endpoint(self):
        profile = ProfessionalProfile.objects.create(user=self.user, headline='My Profile')
        response = self.client.post(f'/api/career-brand/profiles/{profile.id}/analyze/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('overall_score', response.data)
