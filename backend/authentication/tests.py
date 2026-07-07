from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from profiles.models import Profile

User = get_user_model()

class AuthTests(APITestCase):
    def test_register_user_creates_profile(self):
        url = reverse('auth_register')
        data = {
            'username': 'testcandidate',
            'email': 'candidate@test.com',
            'password': 'password123',
            'role': 'candidate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        
        # Verify user exists
        user = User.objects.get(email='candidate@test.com')
        self.assertEqual(user.username, 'testcandidate')
        self.assertEqual(user.role, 'candidate')
        
        # Verify profile was created automatically via serializing
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.name, 'testcandidate')

    def test_login_returns_jwt(self):
        # Create user
        User.objects.create_user(
            username='logintest',
            email='login@test.com',
            password='loginpass123'
        )
        url = reverse('token_obtain_pair')
        data = {
            'email': 'login@test.com',
            'password': 'loginpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
