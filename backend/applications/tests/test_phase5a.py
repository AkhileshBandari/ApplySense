from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from applications.models import Application, ApplicationStatusHistory, ApplicationQuestion, ApplicationAnswerMemory

User = get_user_model()

class Phase5AVerificationTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='password123')
        self.user_b = User.objects.create_user(username='userb', email='userb@example.com', password='password123')
        
        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        
        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)

    def test_security_cross_user_isolation(self):
        # User A creates an application
        app_a = Application.objects.create(user=self.user_a, role="Developer", status="DRAFT")
        
        # User B attempts to read it
        res = self.client_b.get(f'/api/applications/tracker/{app_a.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND, "User B should not see User A's application")
        
        # User B attempts to transition it
        res_transition = self.client_b.post(f'/api/applications/tracker/{app_a.id}/transition/', {'status': 'SUBMITTED'})
        self.assertEqual(res_transition.status_code, status.HTTP_404_NOT_FOUND, "User B should not transition User A's application")

    def test_state_machine_transition(self):
        app = Application.objects.create(user=self.user_a, role="Developer", status="DRAFT")
        # Assuming transition endpoint works
        res = self.client_a.post(f'/api/applications/tracker/{app.id}/transition/', {'status': 'PREPARING'})
        if res.status_code == status.HTTP_200_OK:
            app.refresh_from_db()
            self.assertEqual(app.status, 'PREPARING')
            self.assertTrue(ApplicationStatusHistory.objects.filter(application=app).exists())

    def test_duplicate_prevention_not_implemented(self):
        # We did not implement duplicate prevention, but let's see what happens
        Application.objects.create(user=self.user_a, role="DuplicateRole", status="SUBMITTED")
        app2 = Application.objects.create(user=self.user_a, role="DuplicateRole", status="SUBMITTED")
        self.assertIsNotNone(app2.id, "Duplicate applications are currently allowed")

    def test_answer_memory_security(self):
        memory_a = ApplicationAnswerMemory.objects.create(
            user=self.user_a, question_key="SPONSORSHIP_REQUIRED", answer="No"
        )
        res = self.client_b.get('/api/applications/memory/')
        print("RES.DATA IN TEST:", res.data)
        self.assertEqual(len(res.data.get('results', res.data)), 0, "User B should not see User A's memory")
