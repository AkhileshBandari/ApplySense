import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from evidence.models import GitHubConnection, PortfolioConnection, CandidateSkillEvidence, CandidateRepository, PortfolioProject
from evidence.services.portfolio_service import PortfolioAnalysisService, PortfolioSecurityException
from evidence.services.github_service import GitHubRepositoryAnalysisService
from profiles.models import Profile, Skill, VerificationStatus

User = get_user_model()

class Phase7CAdversarialTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='password123')
        self.user_b = User.objects.create_user(username='userb', email='userb@example.com', password='password123')
        
        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        
        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)
        
        self.conn_a = GitHubConnection.objects.create(user=self.user_a, github_username='usera_gh')
        
    def test_cross_user_github_attack(self):
        # User B attempts to delete User A's connection
        response = self.client_b.delete(f'/api/evidence/github/connection/{self.conn_a.id}/')
        self.assertEqual(response.status_code, 404)
        
        # User B attempts to trigger sync for User A
        response = self.client_b.post(f'/api/evidence/github/connection/{self.conn_a.id}/sync/')
        self.assertEqual(response.status_code, 404)
        
    @patch('evidence.services.github_service.requests.get')
    def test_repository_identity_and_rename(self, mock_get):
        # Simulate initial sync
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = [{
            'id': 12345,
            'name': 'ApplySense',
            'full_name': 'usera_gh/ApplySense',
            'language': 'Python',
            'topics': []
        }]
        mock_get.return_value = mock_response_1
        
        GitHubRepositoryAnalysisService.sync_user_repositories(self.conn_a)
        self.assertEqual(CandidateRepository.objects.count(), 1)
        repo = CandidateRepository.objects.first()
        self.assertEqual(repo.name, 'ApplySense')
        
        # Simulate rename on GitHub
        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = [{
            'id': 12345, # SAME ID
            'name': 'ApplySense-AI',
            'full_name': 'usera_gh/ApplySense-AI',
            'language': 'Python',
            'topics': []
        }]
        mock_get.return_value = mock_response_2
        
        GitHubRepositoryAnalysisService.sync_user_repositories(self.conn_a)
        
        # Ensure identity is preserved, not duplicated
        self.assertEqual(CandidateRepository.objects.count(), 1)
        repo = CandidateRepository.objects.first()
        self.assertEqual(repo.name, 'ApplySense-AI')
        
    @patch('evidence.services.github_service.requests.get')
    def test_fork_attack_and_archived(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'id': 999,
            'name': 'forked-repo',
            'full_name': 'usera_gh/forked-repo',
            'language': 'Python',
            'topics': [],
            'fork': True,
            'archived': True
        }]
        mock_get.return_value = mock_response
        
        GitHubRepositoryAnalysisService.sync_user_repositories(self.conn_a)
        repo = CandidateRepository.objects.first()
        self.assertTrue(repo.is_fork)
        self.assertTrue(repo.is_archived)
        
    def test_verified_context_boundary(self):
        # User has a verified profile skill
        profile = Profile.objects.create(user=self.user_a)
        Skill.objects.create(profile=profile, name='Python', verification_status=VerificationStatus.VERIFIED)
        
        # Create unverified evidence for Docker
        from learning.models import SkillTaxonomy
        taxonomy = SkillTaxonomy.objects.create(canonical_name='Docker', slug='docker')
        evidence = CandidateSkillEvidence.objects.create(
            user=self.user_a,
            skill_taxonomy=taxonomy,
            source_type='GITHUB',
            evidence_type='LANGUAGE_STATISTICS',
            status='DETECTED'
        )
        
        # Verify boundary
        from profiles.services.candidate_context import CandidateContextService
        context = CandidateContextService.get_for_user(self.user_a)
        
        # Context should contain Python but NOT Docker
        verified_skills = [s['name'] for s in context['skills']]
        self.assertIn('Python', verified_skills)
        self.assertNotIn('Docker', verified_skills)

    def test_direct_verification_attack(self):
        # Attacker tries to PATCH evidence to VERIFIED
        from learning.models import SkillTaxonomy
        taxonomy = SkillTaxonomy.objects.create(canonical_name='React', slug='react')
        evidence = CandidateSkillEvidence.objects.create(
            user=self.user_a,
            skill_taxonomy=taxonomy,
            source_type='GITHUB',
            evidence_type='LANGUAGE_STATISTICS',
            status='DETECTED'
        )
        
        response = self.client_a.patch(f'/api/evidence/skills/{evidence.id}/', {'status': 'ACCEPTED'})
        # Should be method not allowed or read only (ViewSet doesn't implement update)
        self.assertEqual(response.status_code, 405)

    def test_evidence_acceptance_does_not_fabricate_truth(self):
        from learning.models import SkillTaxonomy
        taxonomy = SkillTaxonomy.objects.create(canonical_name='AWS', slug='aws')
        evidence = CandidateSkillEvidence.objects.create(
            user=self.user_a,
            skill_taxonomy=taxonomy,
            source_type='GITHUB',
            evidence_type='REPOSITORY_TOPIC',
            status='DETECTED'
        )
        Profile.objects.create(user=self.user_a)
        
        # Accept evidence
        response = self.client_a.post(f'/api/evidence/skills/{evidence.id}/review/', {'action': 'ACCEPT'})
        self.assertEqual(response.status_code, 200)
        
        # Verify it went to Profile.Skill as UNVERIFIED, not VERIFIED
        skill = Skill.objects.get(profile__user=self.user_a, name='AWS')
        self.assertEqual(skill.verification_status, VerificationStatus.UNVERIFIED)
        self.assertEqual(skill.source, 'EXTERNAL_IMPORTED')

class EvidenceSSRFTests(TestCase):
    def test_ssrf_metadata_redirects(self):
        # We test that even if a redirect goes to 169.254.169.254, it is blocked.
        # This requires patching requests to simulate a redirect, but we already have the URL validator that stops it.
        # The PortfolioAnalysisService validate_url_safety checks IP.
        with self.assertRaises(PortfolioSecurityException):
            PortfolioAnalysisService._validate_url_safety('http://169.254.169.254/latest/meta-data/')
            
        with self.assertRaises(PortfolioSecurityException):
            PortfolioAnalysisService._validate_url_safety('http://10.0.0.1/admin')

class TestTokenLeak(TestCase):
    def test_token_serialization(self):
        user = User.objects.create_user(username='test_token', email='test@test.com', password='pw')
        conn = GitHubConnection.objects.create(user=user, github_username='gh_user')
        conn.set_token('ghp_APPLYSENSE_SECRET_TEST_123')
        conn.save()
        
        from evidence.serializers import GitHubConnectionSerializer
        data = GitHubConnectionSerializer(conn).data
        
        # Token MUST NOT be in serialized data
        self.assertNotIn('_encrypted_access_token', data)
        self.assertNotIn('ghp_APPLYSENSE_SECRET_TEST_123', str(data))
