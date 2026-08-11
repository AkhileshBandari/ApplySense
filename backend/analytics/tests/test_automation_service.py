from django.test import TestCase
from django.contrib.auth import get_user_model
from applications.models import Application
from automation.models import AutoApplyRun, AutoApplyRunItem, UserActionRequired
from jobs.models import Job
from analytics.services.automation_service import get_automation_analytics

User = get_user_model()

class AutomationServiceTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='pw')

    def test_auto_vs_manual(self):
        job1 = Job.objects.create(title="Job 1", company="Tech 1", source_job_id="1", description="test")
        job2 = Job.objects.create(title="Job 2", company="Tech 2", source_job_id="2", description="test")
        
        # Manual
        Application.objects.create(user=self.user_a, job=job1, status='SUBMITTED')
        # Auto
        Application.objects.create(user=self.user_a, job=job2, status='SUBMITTED', application_mode='AUTO_TAILORED')
        
        data = get_automation_analytics(self.user_a, {})
        
        self.assertEqual(data['manual_vs_auto']['manual']['submitted'], 1)
        self.assertEqual(data['manual_vs_auto']['auto']['submitted'], 1)

    def test_automation_success_rate(self):
        run = AutoApplyRun.objects.create(user=self.user_a)
        
        job = Job.objects.create(title="Job 1", company="Tech 1", source_job_id="1", description="test")
        
        # 10 execution attempts
        for i in range(10):
            if i < 6:
                # 6 verified success
                AutoApplyRunItem.objects.create(run=run, job=job, stage='EXECUTION', decision='SUCCESS')
            elif i < 8:
                # 2 User Action Required (stage=EXECUTION, decision=FAILED_UAR)
                AutoApplyRunItem.objects.create(run=run, job=job, stage='EXECUTION', decision='FAILED_UAR')
            elif i < 9:
                # 1 failed
                AutoApplyRunItem.objects.create(run=run, job=job, stage='EXECUTION', decision='FAILED')
            else:
                # 1 submission unknown
                AutoApplyRunItem.objects.create(run=run, job=job, stage='EXECUTION', decision='UNKNOWN')

        data = get_automation_analytics(self.user_a, {})
        
        self.assertEqual(data['automation_success']['attempts'], 10)
        self.assertEqual(data['automation_success']['success'], 6)
        self.assertEqual(data['automation_success']['success_rate'], 60.0)

    def test_policy_blocks(self):
        run = AutoApplyRun.objects.create(user=self.user_a)
        job = Job.objects.create(title="Job 1", company="Tech 1", source_job_id="1", description="test")
        
        AutoApplyRunItem.objects.create(run=run, job=job, stage='POLICY', decision='BLOCKED', reason_code='SPONSORSHIP_REQUIRED')
        AutoApplyRunItem.objects.create(run=run, job=job, stage='POLICY', decision='BLOCKED', reason_code='SPONSORSHIP_REQUIRED')
        AutoApplyRunItem.objects.create(run=run, job=job, stage='POLICY', decision='BLOCKED', reason_code='BLACKLISTED_COMPANY')
        
        data = get_automation_analytics(self.user_a, {})
        
        self.assertEqual(len(data['policy_blocks']), 2)
        
        # Order is by count descending
        self.assertEqual(data['policy_blocks'][0]['reason'], 'SPONSORSHIP_REQUIRED')
        self.assertEqual(data['policy_blocks'][0]['count'], 2)
        
        self.assertEqual(data['policy_blocks'][1]['reason'], 'BLACKLISTED_COMPANY')
        self.assertEqual(data['policy_blocks'][1]['count'], 1)

    def test_user_action_reasons(self):
        app1 = Application.objects.create(user=self.user_a, job=Job.objects.create(title="J1", company="C1", source_job_id="1", description="test"), status='SUBMITTED')
        app2 = Application.objects.create(user=self.user_a, job=Job.objects.create(title="J2", company="C2", source_job_id="2", description="test"), status='SUBMITTED')
        app3 = Application.objects.create(user=self.user_a, job=Job.objects.create(title="J3", company="C3", source_job_id="3", description="test"), status='SUBMITTED')
        UserActionRequired.objects.create(user=self.user_a, reason='CAPTCHA_CHALLENGE', application=app1)
        UserActionRequired.objects.create(user=self.user_a, reason='CAPTCHA_CHALLENGE', application=app2)
        UserActionRequired.objects.create(user=self.user_a, reason='OTP_REQUIRED', application=app3)
        
        data = get_automation_analytics(self.user_a, {})
        
        self.assertEqual(len(data['user_actions']), 2)
        self.assertEqual(data['user_actions'][0]['reason'], 'CAPTCHA_CHALLENGE')
        self.assertEqual(data['user_actions'][0]['count'], 2)
        self.assertEqual(data['user_actions'][1]['reason'], 'OTP_REQUIRED')
        self.assertEqual(data['user_actions'][1]['count'], 1)
