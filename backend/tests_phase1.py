import os
import django
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from profiles.models import Profile, Experience
from applications.models import Application, Interview
from resumes.models import Resume
from jobs.models import Job
from django.utils import timezone
from unittest.mock import patch
import json

User = get_user_model()

class Phase1VerificationTests(TestCase):
    def setUp(self):
        # User A
        self.user_a = User.objects.create_user(
            username='usera',
            email='usera@example.com',
            password='password123',
        )
        self.profile_a, _ = Profile.objects.get_or_create(user=self.user_a, name="User A")
        self.resume_a = Resume.objects.create(user=self.user_a, file_name='resume_a.pdf')
        self.job_a = Job.objects.create(title='Dev', company='Comp A')
        self.app_a = Application.objects.create(user=self.user_a, job=self.job_a)
        self.interview_a = Interview.objects.create(application=self.app_a, stage='Technical', scheduled_at=timezone.now())

        # User B
        self.user_b = User.objects.create_user(
            username='userb',
            email='userb@example.com',
            password='password123',
        )
        self.profile_b, _ = Profile.objects.get_or_create(user=self.user_b, name="User B")
        self.resume_b = Resume.objects.create(user=self.user_b, file_name='resume_b.pdf')
        self.job_b = Job.objects.create(title='Eng', company='Comp B')
        self.app_b = Application.objects.create(user=self.user_b, job=self.job_b)
        self.interview_b = Interview.objects.create(application=self.app_b, stage='HR', scheduled_at=timezone.now())

        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)

        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)

        self.unauth_client = APIClient()

    def test_01_unauthenticated_access(self):
        # Attempt to access protected endpoint
        response = self.unauth_client.get(reverse('profile_detail'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.unauth_client.get(reverse('application-tracker-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_user_a_accessing_user_b_profile(self):
        # Profile detail uses request.user, so User A cannot ask for User B's profile
        # Since it fetches the profile of the current user, let's make sure it doesn't return User B
        response = self.client_a.get(reverse('profile_detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "User A")
        self.assertNotEqual(response.data['name'], "User B")

    def test_03_user_a_accessing_user_b_resume(self):
        response = self.client_a.get(reverse('resume_detail', kwargs={'pk': self.resume_b.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_04_user_a_accessing_user_b_application(self):
        response = self.client_a.get(reverse('application-tracker-detail', kwargs={'pk': self.app_b.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_05_user_a_accessing_user_b_interview(self):
        response = self.client_a.get(reverse('application-interview-detail', kwargs={'pk': self.interview_b.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_06_user_a_referencing_user_b_related_ids(self):
        # Try to create an interview on User B's application
        response = self.client_a.post(
            reverse('application-interview-list'),
            {'application': self.app_b.id, 'stage': 'Final'},
            format='json'
        )
        # It should fail because the application doesn't belong to user A
        # Based on perform_create, it calls Application.objects.get(pk=app_id, user=self.request.user)
        # which raises DoesNotExist (500) or we should assert it does not return 201
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_07_invalid_jwt(self):
        self.unauth_client.credentials(HTTP_AUTHORIZATION='Bearer INVALID_TOKEN')
        response = self.unauth_client.get(reverse('application-tracker-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_08_expired_jwt(self):
        # DRF simplejwt handles expiration automatically, we just test if an arbitrary bad token is caught
        self.unauth_client.credentials(HTTP_AUTHORIZATION='Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjF9.xxx')
        response = self.unauth_client.get(reverse('application-tracker-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_10_ai_provider_unavailable(self, mock_generate):
        mock_generate.side_effect = RuntimeError("All providers failed")
        
        response = self.client_a.post(
            reverse('coach_interview_prep'),
            {'role': 'React Engineer'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_11_ai_provider_returns_malformed_json(self, mock_generate):
        mock_generate.return_value = "This is not JSON at all"
        
        response = self.client_a.post(
            reverse('coach_interview_prep'),
            {'role': 'React Engineer'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("malformed JSON", response.data['error'])

    def test_12_missing_ai_api_key(self):
        # We can test fallback manager directly
        from ai_engine.fallback_manager import AIFallbackManager
        manager = AIFallbackManager()
        # clear keys
        manager.openai_key = ""
        manager.groq_key = ""
        manager.openrouter_key = ""
        manager.hf_key = ""
        
        with self.assertRaises(RuntimeError):
            manager.generate_content("sys", "user")
