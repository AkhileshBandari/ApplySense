from django.test import TestCase
from jobs.registries import JobSourceRegistry, ApplicationProviderRegistry, ImplementationStatus, CertificationStatus
from applications.services.execution_domain import PreExecutionValidationService
from jobs.models import Job, JobSourceOccurrence
from django.contrib.auth import get_user_model
from applications.models import Application, ApplicationApproval, FormSession, AutomationPolicy

User = get_user_model()

class Phase5ETests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.policy = AutomationPolicy.objects.create(user=self.user)
        
        self.job = Job.objects.create(title="Software Engineer", company="Test Corp", canonical_hash="Test Corp-Software Engineer")
        JobSourceOccurrence.objects.create(job=self.job, source="LinkedIn", source_url="http://linkedin.com/job1")
        
        self.app = Application.objects.create(
            user=self.user,
            job=self.job,
            application_provider="Workday",
            status="READY_TO_SUBMIT",
            snapshot={"fingerprint": "hash123"}
        )
        
        self.approval = ApplicationApproval.objects.create(
            application=self.app,
            approved_by=self.user,
            snapshot_fingerprint="hash123",
            status="VALID"
        )

    def test_registry_capabilities(self):
        source = JobSourceRegistry.get_capability("LinkedIn")
        self.assertTrue(source.discovery_supported)
        self.assertTrue(source.authentication_required)
        
        provider = ApplicationProviderRegistry.get_capability("Workday")
        self.assertTrue(provider.form_detection)
        self.assertFalse(provider.user_confirmed_browser_submit) # Blocked intentionally
        self.assertEqual(provider.certification_status, CertificationStatus.FIXTURE_VERIFIED)

    def test_redetection_validation_blocks_mismatch(self):
        # Create a FormSession with a different provider to simulate MITM redirect or variant
        FormSession.objects.create(
            user=self.user,
            application=self.app,
            provider="Greenhouse", # Mismatch! App says Workday
            url="https://boards.greenhouse.io/test"
        )
        
        is_valid, reason, error_code = PreExecutionValidationService.validate_for_execution(self.user, self.app, "hash123")
        self.assertFalse(is_valid)
        self.assertIn("Re-detection mismatch", reason)

    def test_validation_blocks_unverified_providers(self):
        # Change to a provider that is only REGISTERED
        self.app.application_provider = "Taleo"
        self.app.save()
        
        FormSession.objects.create(
            user=self.user,
            application=self.app,
            provider="Taleo",
            url="https://taleo.net/test"
        )
        
        is_valid, reason, error_code = PreExecutionValidationService.validate_for_execution(self.user, self.app, "hash123")
        self.assertFalse(is_valid)
        self.assertIn("not implemented or blocked", reason)

    def test_job_deduplication(self):
        occurrences = self.job.occurrences.all()
        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0].source, "LinkedIn")
