from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from applications.models import Application
from jobs.models import Job

User = get_user_model()

class AnalyticsAPITests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='pw')
        self.user_b = User.objects.create_user(username='userb', email='userb@example.com', password='pw')
        
        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        
        self.client_unauth = APIClient()

    def test_unauthenticated(self):
        resp = self.client_unauth.get('/api/analytics/overview/')
        self.assertEqual(resp.status_code, 401)

    def test_user_id_injection(self):
        job = Job.objects.create(title="J1", company="C1", source_job_id="1", description="test")
        Application.objects.create(user=self.user_b, job=job, status='SUBMITTED')
        
        # User A tries to get User B's data
        resp = self.client_a.get(f'/api/analytics/overview/?user_id={self.user_b.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['applications_submitted'], 0) # Should be ignored and scoped to user A

    def test_n_plus_one_queries(self):
        job = Job.objects.create(title="J1", company="C1", source_job_id="1", description="test")
        for i in range(50):
            Application.objects.create(user=self.user_a, job=job, status='SUBMITTED')
            
        with self.assertNumQueries(2):
            # 1 for applications base qs
            # 1 for match_qs count
            # 1 for Application aggregates
            # 1 for session/auth (varies)
            resp = self.client_a.get('/api/analytics/overview/')
            self.assertEqual(resp.status_code, 200)

    def test_invalid_date_format(self):
        resp = self.client_a.get('/api/analytics/overview/?time_range=CUSTOM&start_date=invalid')
        self.assertEqual(resp.status_code, 400)
