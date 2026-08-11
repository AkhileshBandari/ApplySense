from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class ProfileApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='password123',
            role='candidate',
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_can_be_updated_and_skills_created(self):
        response = self.client.patch(
            reverse('profile_detail'),
            {'name': 'Ada Lovelace', 'location': 'London'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Ada Lovelace')
        self.assertEqual(response.data['location'], 'London')

        skill_response = self.client.post(
            reverse('skill-list'),
            {'name': 'Django'},
            format='json',
        )

        self.assertEqual(skill_response.status_code, status.HTTP_201_CREATED)
        # Verify skill was created via nested serializer
        list_response = self.client.get('/api/profile/skills/')
        self.assertEqual(list_response.data['results'][0]['name'], 'Django')
