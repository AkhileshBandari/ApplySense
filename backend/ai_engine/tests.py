from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class CoachEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='coachuser',
            email='coach@example.com',
            password='password123',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)



    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_interview_prep_endpoint_success(self, mock_generate):
        mock_generate.return_value = '{"behavioral_questions": ["Tell me about..."], "technical_questions": [], "tips": []}'
        response = self.client.post(
            reverse('coach_interview_prep'),
            {'role': 'Platform Engineer', 'experience': '3 years'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('behavioral_questions', response.data)

    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_endpoints_return_502_on_ai_failure(self, mock_generate):
        mock_generate.side_effect = RuntimeError("All providers failed")
        response = self.client.post(
            reverse('coach_interview_prep'),
            {'role': 'Platform Engineer'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn('error', response.data)
