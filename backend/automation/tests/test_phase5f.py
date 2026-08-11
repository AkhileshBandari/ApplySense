
from django.test import TestCase
from django.utils import timezone
from authentication.models import User
from applications.models import Application, ApplicationExecution, AutomationPolicy
from automation.models import AutoApplyConfiguration, AutoApplyRun, UserActionRequired
from automation.services.server_browser import ServerBrowserExecutionService
from applications.services.execution_domain import ExecutionReservationService, ServerExecutionCapabilityResolver
from applications.constants import ExecutionStatus
from jobs.registries import ApplicationProviderRegistry, PlatformCapability, ImplementationStatus
from automation.tests.mock_ats import MockATSServer

class Phase5FTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_5f", email="test_5f@example.com", password="password123")
        self.policy = AutomationPolicy.objects.create(
            user=self.user,
            automation_enabled=True,
            daily_application_limit=5
        )
        self.config = AutoApplyConfiguration.objects.create(
            user=self.user,
            auto_apply_enabled=True,
            daily_application_limit=2
        )
        self.application = Application.objects.create(
            user=self.user,
            application_provider="Generic ATS",
            status="READY_TO_SUBMIT",
            application_url="http://localhost:8099/success"
        )
        
        # We need a capability we can control
        self.mock_capability = PlatformCapability(
            server_execution_allowed=True,
            implementation_status=ImplementationStatus.CERTIFIED
        )

    def test_server_execution_resolver(self):
        # Test disabled server execution
        disabled_cap = PlatformCapability(
            server_execution_allowed=False,
            implementation_status=ImplementationStatus.CERTIFIED
        )
        mode, reason = ServerExecutionCapabilityResolver.resolve(
            application=self.application,
            provider="Greenhouse",
            source="LinkedIn",
            provider_capability=disabled_cap,
            policy=self.policy,
            authorization_state='UNVERIFIED'
        )
        self.assertEqual(mode, 'USER_ACTION_REQUIRED')
        
        # Test permitted execution
        mode, reason = ServerExecutionCapabilityResolver.resolve(
            application=self.application,
            provider="Greenhouse",
            source="LinkedIn",
            provider_capability=self.mock_capability,
            policy=self.policy,
            authorization_state='UNVERIFIED'
        )
        self.assertEqual(mode, 'SERVER_BROWSER')
        
        # Test indeed unauthorized
        mode, reason = ServerExecutionCapabilityResolver.resolve(
            application=self.application,
            provider="",
            source="Indeed",
            provider_capability=self.mock_capability,
            policy=self.policy,
            authorization_state='UNVERIFIED'
        )
        self.assertEqual(mode, 'USER_ACTION_REQUIRED')

    def test_atomic_limits_enforced(self):
        # Daily limit is 2 based on config
        success1, exec1, err1 = ExecutionReservationService.reserve_execution_slot(self.user, self.application, idempotency_key="idemp1")
        self.assertTrue(success1)
        
        app2 = Application.objects.create(user=self.user, status="READY_TO_SUBMIT")
        success2, exec2, err2 = ExecutionReservationService.reserve_execution_slot(self.user, app2, idempotency_key="idemp2")
        self.assertTrue(success2)
        
        app3 = Application.objects.create(user=self.user, status="READY_TO_SUBMIT")
        success3, exec3, err3 = ExecutionReservationService.reserve_execution_slot(self.user, app3, idempotency_key="idemp3")
        self.assertFalse(success3)
        self.assertEqual(err3, 'DAILY_LIMIT_REACHED')
        
    def test_execution_already_active(self):
        success1, exec1, err1 = ExecutionReservationService.reserve_execution_slot(self.user, self.application, idempotency_key="idemp1")
        self.assertTrue(success1)
        
        # Trying to reserve the same application again should fail
        success2, exec2, err2 = ExecutionReservationService.reserve_execution_slot(self.user, self.application, idempotency_key="idemp_another")
        self.assertFalse(success2)
        self.assertEqual(err2, 'EXECUTION_ALREADY_ACTIVE')

class Phase5FPlaywrightTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = MockATSServer(port=8099)
        cls.server.start()
        
    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="test_playwright", email="test_playwright@example.com", password="password123")
        self.application = Application.objects.create(
            user=self.user,
            application_provider="Mock Provider",
            status="READY_TO_SUBMIT"
        )
        
    def test_playwright_success(self):
        self.application.application_url = "http://localhost:8099/success"
        self.application.save()
        
        execution = ApplicationExecution.objects.create(
            user=self.user,
            application=self.application,
            execution_status=ExecutionStatus.READY,
            provider="Mock Provider",
            application_mode="SERVER_BROWSER"
        )
        
        service = ServerBrowserExecutionService()
        result = service.execute(execution)
        
        # Execute should succeed
        self.assertTrue(result)
        
        # Check that receipt was created and execution marked success
        execution.refresh_from_db()
        self.assertEqual(execution.execution_status, ExecutionStatus.SUCCEEDED)
        self.assertTrue(execution.receipts.exists())
        self.assertEqual(self.application.status, 'SUBMITTED')

    def test_playwright_captcha_blocked(self):
        self.application.application_url = "http://localhost:8099/captcha"
        self.application.save()
        
        execution = ApplicationExecution.objects.create(
            user=self.user,
            application=self.application,
            execution_status=ExecutionStatus.READY,
            provider="Mock Provider",
            application_mode="SERVER_BROWSER"
        )
        
        service = ServerBrowserExecutionService()
        result = service.execute(execution)
        
        # Execute should fail
        self.assertFalse(result)
        
        # Execution status should be FAILED
        execution.refresh_from_db()
        self.assertEqual(execution.execution_status, ExecutionStatus.FAILED)
        self.assertIn("CAPTCHA detected", execution.failure_reason)
