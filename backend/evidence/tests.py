import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from evidence.models import GitHubConnection, PortfolioConnection, CandidateSkillEvidence
from evidence.services.portfolio_service import PortfolioAnalysisService, PortfolioSecurityException

User = get_user_model()

class PortfolioSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser_db', email='test@example.com', password='password123')
        self.connection = PortfolioConnection.objects.create(user=self.user, portfolio_url='https://example.com')
        
    def test_ssrf_protection_localhost(self):
        with self.assertRaises(PortfolioSecurityException):
            PortfolioAnalysisService._validate_url_safety('http://localhost:8000')
            
    def test_ssrf_protection_private_ip(self):
        with self.assertRaises(PortfolioSecurityException):
            PortfolioAnalysisService._validate_url_safety('http://192.168.1.1/admin')
            
    def test_ssrf_protection_link_local(self):
        with self.assertRaises(PortfolioSecurityException):
            PortfolioAnalysisService._validate_url_safety('http://169.254.169.254/latest/meta-data/')
            
    def test_ssrf_protection_scheme(self):
        with self.assertRaises(PortfolioSecurityException):
            PortfolioAnalysisService._validate_url_safety('file:///etc/passwd')
            
    def test_ssrf_protection_valid(self):
        # Should not raise exception
        PortfolioAnalysisService._validate_url_safety('https://github.com')

class GitHubIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser_db', email='test@example.com', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def test_create_connection(self):
        response = self.client.post('/api/evidence/github/connection/', {
            'github_username': 'testuser',
            'access_token': 'fake_token'
        })
        self.assertEqual(response.status_code, 201)
        
        conn = GitHubConnection.objects.get(user=self.user)
        self.assertEqual(conn.github_username, 'testuser')
        self.assertEqual(conn.get_token(), 'fake_token')
        
        # Second creation should overwrite, not duplicate
        response = self.client.post('/api/evidence/github/connection/', {
            'github_username': 'testuser2'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GitHubConnection.objects.count(), 1)
        
    @patch('evidence.services.github_service.requests.get')
    def test_github_sync_rate_limit(self, mock_get):
        conn = GitHubConnection.objects.create(user=self.user, github_username='testuser')
        
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = 'API rate limit exceeded'
        mock_get.return_value = mock_response
        
        response = self.client.post(f'/api/evidence/github/connection/{conn.id}/sync/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'RATE_LIMITED')
        
    @patch('evidence.services.github_service.requests.get')
    def test_github_sync_success_and_idempotency(self, mock_get):
        conn = GitHubConnection.objects.create(user=self.user, github_username='testuser')
        
        # Mock successful repos payload
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 123,
                'name': 'test-repo',
                'full_name': 'testuser/test-repo',
                'language': 'Python',
                'topics': ['django', 'docker']
            }
        ]
        mock_get.return_value = mock_response
        
        # First Sync
        response = self.client.post(f'/api/evidence/github/connection/{conn.id}/sync/')
        self.assertEqual(response.status_code, 200)
        
        # Check evidence was created
        evidence = CandidateSkillEvidence.objects.filter(user=self.user)
        self.assertEqual(evidence.count(), 3) # Python, django, docker
        
        # Second Sync - should update, not create new duplicates
        response = self.client.post(f'/api/evidence/github/connection/{conn.id}/sync/')
        self.assertEqual(response.status_code, 200)
        
        # Evidence count should remain 3
        evidence = CandidateSkillEvidence.objects.filter(user=self.user)
        self.assertEqual(evidence.count(), 3)
