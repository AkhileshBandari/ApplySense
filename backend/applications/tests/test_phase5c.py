from django.test import TestCase
from django.contrib.auth import get_user_model
from applications.models import Application, FormSession, DetectedApplicationForm, DetectedApplicationFormField, AutomationPolicy
from jobs.models import Job
from applications.services.form_intelligence import FormIntelligenceService
import json

User = get_user_model()

class Phase5CFormIntelligenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_5c', email='test5c@example.com', password='password123')
        self.job = Job.objects.create(title='Software Engineer', company='TechCorp')
        self.application = Application.objects.create(user=self.user, job=self.job)
        
        self.policy = AutomationPolicy.objects.create(
            user=self.user,
            automation_enabled=True,
            require_review_before_submit=True,
            minimum_match_score=0
        )

    def test_session_initialization(self):
        session = FormIntelligenceService.initialize_session(
            self.user, 
            self.application.id, 
            'Greenhouse', 
            'https://boards.greenhouse.io/techcorp/jobs/123'
        )
        self.assertEqual(session.provider, 'Greenhouse')
        self.assertEqual(session.status, 'DETECTED')
        
    def test_form_schema_processing(self):
        session = FormIntelligenceService.initialize_session(self.user, self.application.id, 'Greenhouse', 'https://url.com')
        
        # Mock payload from extension
        fields_data = [
            {'id': 'first_name', 'label': 'First Name', 'name': 'firstname', 'type': 'text'},
            {'id': 'sponsorship', 'label': 'Do you require sponsorship?', 'type': 'select', 'options': ['Yes', 'No']},
            {'id': 'terms', 'label': 'I agree to terms', 'type': 'checkbox', 'required': True}
        ]
        
        detected_form = FormIntelligenceService.process_form_schema(session, fields_data)
        
        self.assertEqual(detected_form.fields.count(), 3)
        
        # Verify classification and safe autofill constraints
        first_name_field = detected_form.fields.get(normalized_key='FIRST_NAME')
        self.assertEqual(first_name_field.resolution_status, 'USER_INPUT_REQUIRED') # Unanswered so it falls back to required
        self.assertTrue(first_name_field.requires_review)
        
        sponsorship_field = detected_form.fields.get(normalized_key='SPONSORSHIP_REQUIRED')
        self.assertEqual(sponsorship_field.resolution_status, 'USER_INPUT_REQUIRED')
        self.assertTrue(sponsorship_field.requires_review)

        consent_field = detected_form.fields.get(normalized_key='LEGAL_CONSENT')
        self.assertEqual(consent_field.resolution_status, 'NEVER_AUTOFILL')
        self.assertIsNone(consent_field.proposed_value)

    def test_cross_user_isolation(self):
        user2 = User.objects.create_user(username='hacker', password='password123')
        
        session = FormIntelligenceService.initialize_session(self.user, self.application.id, 'Greenhouse', 'https://url.com')
        
        # User 2 tries to process User 1's session (should raise error in a view, but testing service direct access is safe)
        with self.assertRaises(Exception):
            session_wrong_user = FormSession.objects.get(id=session.id, user=user2)

    def test_policy_blocks_autofill(self):
        self.policy.global_pause = True
        self.policy.save()
        
        session = FormIntelligenceService.initialize_session(self.user, self.application.id, 'Greenhouse', 'https://url.com')
        
        fields_data = [
            {'id': 'first_name', 'label': 'First Name', 'name': 'firstname', 'type': 'text'},
        ]
        
        detected_form = FormIntelligenceService.process_form_schema(session, fields_data)
        
        # Field should be PENDING because policy blocked processing
        first_name_field = detected_form.fields.get(normalized_key='FIRST_NAME')
        self.assertEqual(first_name_field.resolution_status, 'PENDING')

    def test_secret_fields_blocked(self):
        session = FormIntelligenceService.initialize_session(self.user, self.application.id, 'Greenhouse', 'https://url.com')
        fields_data = [
            {'id': 'f1', 'label': 'Enter your OTP', 'name': 'otp_code', 'type': 'text'},
            {'id': 'f2', 'label': 'Account Password', 'name': 'password', 'type': 'password'},
        ]
        detected_form = FormIntelligenceService.process_form_schema(session, fields_data)
        
        for field in detected_form.fields.all():
            self.assertEqual(field.normalized_key, 'SECRET')
            self.assertEqual(field.resolution_status, 'NEVER_AUTOFILL')
            self.assertIsNone(field.proposed_value)
            self.assertTrue(field.requires_review)

    def test_misleading_labels_classification(self):
        session = FormIntelligenceService.initialize_session(self.user, self.application.id, 'Greenhouse', 'https://url.com')
        fields_data = [
            {'id': 'f1', 'label': 'LinkedIn experience (years)', 'name': 'linkedin_exp', 'type': 'text'},
            {'id': 'f2', 'label': 'Phone interview availability', 'name': 'phone_avail', 'type': 'text'},
            {'id': 'f3', 'label': 'LinkedIn Profile', 'name': 'linkedin', 'type': 'text'},
        ]
        detected_form = FormIntelligenceService.process_form_schema(session, fields_data)
        
        f1 = detected_form.fields.get(provider_field_id='f1')
        self.assertEqual(f1.normalized_key, 'UNKNOWN_CUSTOM')
        
        f2 = detected_form.fields.get(provider_field_id='f2')
        self.assertEqual(f2.normalized_key, 'UNKNOWN_CUSTOM')
        
        f3 = detected_form.fields.get(provider_field_id='f3')
        self.assertEqual(f3.normalized_key, 'LINKEDIN_URL')

    def test_placeholder_dropdown(self):
        session = FormIntelligenceService.initialize_session(self.user, self.application.id, 'Greenhouse', 'https://url.com')
        # Simulate a field where AnswerResolver returned 'Yes' but dropdown has placeholders
        
        fields_data = [
            {'id': 'f1', 'label': 'Do you require sponsorship?', 'type': 'select', 'options': ['Select...', 'Yes', 'No', 'Please choose']},
        ]
        
        # Manually force the resolver to return something via mocking, or just test _map_option directly
        mapped_yes = FormIntelligenceService._map_option('Yes', ['Select...', 'Yes', 'No', 'Please choose'])
        self.assertEqual(mapped_yes, 'Yes')
        
        # Test placeholder behavior
        mapped_select = FormIntelligenceService._map_option('Select...', ['Select...', 'Yes', 'No'])
        self.assertIsNone(mapped_select)
