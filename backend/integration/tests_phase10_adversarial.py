from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from career_integration.models import (
    CareerOperatingState, CareerIntegrationSnapshot, CareerOutcomeEvent, CanonicalOutcomeEvent, 
    DomainName, DomainStateStatus, DataTrustLevel, UserActionItem, SystemBlocker, SystemState
)
from career_integration.services.reconciliation_service import CareerReconciliationService
from career_integration.services.snapshot_service import IntegrationSnapshotService
from career_integration.services.os_orchestrator import OSOrchestratorService
from career_integration.services.action_center import ActionCenterService
from profiles.models import Profile
from automation.models import AutoApplyRun

import json

User = get_user_model()

class Phase10AdversarialTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="usera", email="a@example.com", password="password")
        self.user_b = User.objects.create_user(username="userb", email="b@example.com", password="password")
        
        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        
        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)
        
        self.unauth_client = APIClient()
        
        # Base setup for OS state
        OSOrchestratorService.evaluate_os_readiness(self.user_a)
        self.state_a = CareerOperatingState.objects.get(user=self.user_a)
        self.snapshot_a = IntegrationSnapshotService.generate_snapshot(self.user_a)

    def test_domain_ownership(self):
        # Phase 10 must not provide any endpoints to mutate authoritative upstream models
        # Ensure that no view allows POSTing to Profile, AutoApplyRun etc via the Integration APIs
        res = self.client_a.post('/api/career-integration/state/current/', data={"profile": {"name": "Hacked"}}, format='json')
        self.assertEqual(res.status_code, 405) # Read-only
        
    def test_authentication(self):
        # Check all endpoints
        for path in [
            '/api/career-integration/state/current/',
            '/api/career-integration/snapshot/',
            '/api/career-integration/events/',
            '/api/career-integration/action-center/'
        ]:
            res = self.unauth_client.get(path)
            self.assertEqual(res.status_code, 401)
            res = self.unauth_client.post(path, data={})
            self.assertEqual(res.status_code, 401)
            res = self.unauth_client.patch(path, data={})
            self.assertEqual(res.status_code, 401)
            res = self.unauth_client.delete(path)
            self.assertEqual(res.status_code, 401)

    def test_cross_user_isolation(self):
        # User B accessing User A state
        res = self.client_b.get(f'/api/career-integration/snapshot/{self.snapshot_a.id}/')
        self.assertEqual(res.status_code, 404)
        
        # Create an action item for A
        action = UserActionItem.objects.create(
            user=self.user_a,
            source_domain=DomainName.CONTEXT,
            blocker_type=SystemBlocker.PROFILE_INCONSISTENT,
            title="Fix Profile"
        )
        res = self.client_b.get(f'/api/career-integration/action-center/{action.id}/')
        self.assertEqual(res.status_code, 404)

    def test_client_authority_attack(self):
        # Client trying to inject readiness score
        res = self.client_a.patch('/api/career-integration/state/current/', {
            "overall_readiness_score": 100,
            "current_os_state": "EXECUTION_READY"
        })
        self.assertEqual(res.status_code, 405) # ReadOnly API
        
        self.state_a.refresh_from_db()
        self.assertNotEqual(self.state_a.current_os_state, SystemState.EXECUTION_READY)

    def test_trust_level_escalation(self):
        # Client trying to edit a snapshot to escalate trust level
        res = self.client_a.patch(f'/api/career-integration/snapshot/{self.snapshot_a.id}/', {
            "trust_level_map": {"candidate_facts": "VERIFIED", "career_pathways": "VERIFIED"}
        }, format='json')
        self.assertEqual(res.status_code, 405)
        
    def test_hypothetical_data_firewall(self):
        # Snapshots enforce trust levels
        trust_levels = self.snapshot_a.trust_level_map
        self.assertEqual(trust_levels.get("career_pathways"), DataTrustLevel.HYPOTHETICAL)

    def test_verified_candidate_context_attack(self):
        # Attempt to modify context through ActionCenter resolution
        action = UserActionItem.objects.create(
            user=self.user_a,
            source_domain=DomainName.CONTEXT,
            blocker_type=SystemBlocker.PROFILE_INCONSISTENT,
            title="Fix Profile"
        )
        res = self.client_a.patch(f'/api/career-integration/action-center/{action.id}/', {
            "resolution_data": {"name": "Hacked Fact"}
        }, format='json')
        # Resolving should not mutate Profile data. It's just an acknowledgment.
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Profile.objects.filter(name="Hacked Fact").exists())

    def test_system_state_determinism(self):
        # State A (No profile) -> ONBOARDING
        self.assertEqual(self.state_a.current_os_state, SystemState.ONBOARDING)
        
        # State B (Profile added)
        Profile.objects.create(user=self.user_a, name="Test")
        OSOrchestratorService.evaluate_os_readiness(self.user_a)
        self.state_a.refresh_from_db()
        self.assertEqual(self.state_a.current_os_state, SystemState.PROFILE_READY)

    def test_readiness_gate_attack(self):
        res = self.client_a.post('/api/career-integration/state/current/force_execution/', data={})
        self.assertEqual(res.status_code, 404) # Non-existent route
        
    def test_auto_apply_authorization_attack(self):
        # Action Center cannot CREATE AutoApplyRuns or authorize them
        res = self.client_a.post('/api/career-integration/action-center/', {
            "title": "Authorize AutoApply",
            "blocker_type": "USER_ACTION_REQUIRED"
        }, format='json')
        self.assertIn(res.status_code, [400, 405]) # Will fail because POST is not properly supported or readonly

    def test_action_center_idempotency(self):
        ActionCenterService.recalculate_actions(self.user_a)
        ActionCenterService.recalculate_actions(self.user_a)
        ActionCenterService.recalculate_actions(self.user_a)
        
        missing_skills = UserActionItem.objects.filter(
            user=self.user_a, blocker_type=SystemBlocker.MISSING_VERIFIED_SKILL, is_resolved=False
        )
        # Should only be exactly 1 despite repeated evaluation
        self.assertEqual(missing_skills.count(), 1)

    def test_pagination_attack(self):
        # Attempt to get massive page size
        res = self.client_a.get('/api/career-integration/action-center/?page_size=1000000')
        # Paginator bounds this safely
        self.assertLessEqual(len(res.json()['results']), 100)
        
    def test_privacy_attack(self):
        res = self.client_a.get('/api/career-integration/state/current/')
        data = json.dumps(res.json())
        self.assertNotIn("password", data.lower())
        self.assertNotIn("token", data.lower())
        self.assertNotIn("jwt", data.lower())

    def test_n_plus_1_query_attack(self):
        # We'll assert num queries to ensure it's performant
        # Since it fetches the paginated queryset, num queries should be stable regardless of page size
        # Usually 3 or 4: Auth, Count, Query
        with self.assertNumQueries(2): 
            self.client_a.get('/api/career-integration/action-center/')
