from django.test import TestCase
from django.contrib.auth import get_user_model
from applications.models import Application, ApplicationAnswerMemory, ApplicationQuestion
from applications.services.duplicate_service import ApplicationDuplicateService
from applications.services.answer_resolver import ApplicationAnswerResolver
from resumes.models import Resume, ResumeVersion
from jobs.models import Job
from django.core.exceptions import ValidationError

User = get_user_model()

class Phase5ARepairsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.resume = Resume.objects.create(user=self.user, file_name='resume.pdf')
        self.version = ResumeVersion.objects.create(user=self.user, source_resume=self.resume, version_name='v1')
        self.job = Job.objects.create(title="Software Engineer", company="TechCorp")

    def test_duplicate_service_no_duplicates(self):
        # User has no apps
        status = ApplicationDuplicateService.check_duplicate(self.user, job_id=self.job.id)
        self.assertEqual(status, 'NO_DUPLICATE')

    def test_duplicate_service_draft_ignored(self):
        # Drafts don't count as duplicates
        Application.objects.create(user=self.user, job=self.job, status='DRAFT')
        status = ApplicationDuplicateService.check_duplicate(self.user, job_id=self.job.id)
        self.assertEqual(status, 'NO_DUPLICATE')

    def test_duplicate_service_previously_applied(self):
        # Submitted app counts
        Application.objects.create(user=self.user, job=self.job, status='SUBMITTED')
        status = ApplicationDuplicateService.check_duplicate(self.user, job_id=self.job.id)
        self.assertEqual(status, 'PREVIOUSLY_APPLIED')

    def test_answer_memory_blocks_passwords(self):
        # Attempt to save a password field
        memory = ApplicationAnswerMemory(user=self.user, question_key='ENTER_PASSWORD', answer='mysecret')
        with self.assertRaises(ValidationError):
            memory.clean()

    def test_answer_resolver_sensitive_questions_blocked(self):
        # Sensitive questions without memory should be USER_INPUT_REQUIRED
        result = ApplicationAnswerResolver.resolve(self.user, "What is your gender?", "DEMOGRAPHIC_OPTIONAL")
        self.assertEqual(result['review_status'], 'USER_INPUT_REQUIRED')
        self.assertEqual(result['source'], 'UNANSWERED')

    def test_answer_resolver_sensitive_questions_allowed_with_memory(self):
        # If user explicitly answered it and saved it, we allow it
        ApplicationAnswerMemory.objects.create(user=self.user, question_key='DEMOGRAPHIC_OPTIONAL', answer='Male', verification_status='VERIFIED')
        result = ApplicationAnswerResolver.resolve(self.user, "What is your gender?", "DEMOGRAPHIC_OPTIONAL")
        self.assertEqual(result['review_status'], 'REVIEW_RECOMMENDED')
        self.assertEqual(result['source'], 'ANSWER_MEMORY')
        self.assertEqual(result['answer'], 'Male')
