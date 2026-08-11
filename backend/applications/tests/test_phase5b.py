from django.test import TestCase
from django.contrib.auth import get_user_model
from applications.models import Application, AutomationPolicy, AutomationRule, PolicyDecision
from applications.services.policy_evaluator import AutomationPolicyEvaluator
from django.utils import timezone

User = get_user_model()

class Phase5BTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        
        self.policy1 = AutomationPolicy.objects.create(
            user=self.user1,
            automation_enabled=True,
            daily_application_limit=2,
            minimum_match_score=80
        )
        
        self.policy2 = AutomationPolicy.objects.create(
            user=self.user2,
            automation_enabled=False # Disabled by default
        )
        
        self.app1 = Application.objects.create(user=self.user1, company='EvilCorp', match_score=85, status='DRAFT')
        self.app2 = Application.objects.create(user=self.user2, company='GoodCorp', match_score=90, status='DRAFT')

    def test_automation_disabled_blocks_user2(self):
        decision = AutomationPolicyEvaluator.evaluate(self.app2)
        self.assertEqual(decision.decision, 'REQUIRE_REVIEW')
        self.assertIn('AUTOMATION_DISABLED', decision.reason_codes)

    def test_global_pause_blocks(self):
        self.policy1.global_pause = True
        self.policy1.save()
        decision = AutomationPolicyEvaluator.evaluate(self.app1)
        self.assertEqual(decision.decision, 'BLOCK')
        self.assertIn('GLOBAL_PAUSE_ACTIVE', decision.reason_codes)

    def test_match_score_too_low(self):
        self.app1.match_score = 70
        self.app1.save()
        decision = AutomationPolicyEvaluator.evaluate(self.app1)
        self.assertEqual(decision.decision, 'BLOCK')
        self.assertIn('MATCH_SCORE_TOO_LOW', decision.reason_codes)

    def test_company_exclusion_rule(self):
        AutomationRule.objects.create(
            policy=self.policy1,
            rule_type='EXCLUDED_COMPANY',
            value={'companies': ['EvilCorp', 'BadCorp']}
        )
        decision = AutomationPolicyEvaluator.evaluate(self.app1)
        self.assertEqual(decision.decision, 'BLOCK')
        self.assertIn('EXCLUDED_COMPANY_MATCHED', decision.reason_codes)

    def test_cross_user_isolation(self):
        # user1 has EvilCorp exclusion, user2 shouldn't be affected (even if they were enabled)
        AutomationRule.objects.create(
            policy=self.policy1,
            rule_type='EXCLUDED_COMPANY',
            value={'companies': ['GoodCorp']}
        )
        
        self.policy2.automation_enabled = True
        self.policy2.save()
        
        decision2 = AutomationPolicyEvaluator.evaluate(self.app2)
        # Shouldn't be blocked by GoodCorp exclusion because that belongs to user1
        self.assertNotIn('EXCLUDED_COMPANY_MATCHED', decision2.reason_codes)
