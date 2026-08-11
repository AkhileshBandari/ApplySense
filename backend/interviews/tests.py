from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import InterviewPlan, MockInterviewSession, InterviewQuestion

User = get_user_model()

class InterviewIntelligenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', email='test@applysense.ai', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_generate_plan(self):
        response = self.client.post('/api/interview-intelligence/plans/generate/', {
            'interview_type': 'TECHNICAL',
            'target_role': 'Backend Engineer'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['target_role'], 'Backend Engineer')
        
    def test_session_start_and_answer(self):
        # Generate Plan
        plan = InterviewPlan.objects.create(user=self.user, interview_type='TECHNICAL')
        session = MockInterviewSession.objects.create(user=self.user, plan=plan)
        
        # Start Session
        response = self.client.post(f'/api/interview-intelligence/sessions/{session.id}/start/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'IN_PROGRESS')
        
        # Create Question Manually (bypassing AI generation for test reliability)
        question = InterviewQuestion.objects.create(
            session=session, plan=plan, question_type='TECHNICAL',
            question_text='What is a decorator?', sequence=1
        )
        
        # Answer Question
        ans_response = self.client.post(f'/api/interview-intelligence/sessions/{session.id}/answer/', {
            'question_id': question.id,
            'response_text': 'A decorator takes a function and returns a new function.'
        })
        self.assertEqual(ans_response.status_code, status.HTTP_200_OK)
        self.assertIn('evaluation', ans_response.data)

    def test_complete_session(self):
        plan = InterviewPlan.objects.create(user=self.user, interview_type='TECHNICAL')
        session = MockInterviewSession.objects.create(user=self.user, plan=plan, status='IN_PROGRESS')
        
        res = self.client.post(f'/api/interview-intelligence/sessions/{session.id}/complete/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'COMPLETED')
