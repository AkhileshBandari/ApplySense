from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from career_integration.models import (
    CareerOperatingState, CareerIntegrationSnapshot, CareerOutcomeEvent, CanonicalOutcomeEvent, 
    DomainName, DomainStateStatus, DataTrustLevel
)
from career_integration.services.reconciliation_service import CareerReconciliationService
from career_integration.services.snapshot_service import IntegrationSnapshotService

User = get_user_model()

class CareerIntegrationAdversarialTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="usera", email="a@example.com", password="password")
        self.user_b = User.objects.create_user(username="userb", email="b@example.com", password="password")
        
        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)
        
        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)
        
        self.unauth_client = APIClient()
        
        self.state_a = CareerOperatingState.objects.create(
            user=self.user_a, overall_readiness_score=50, execution_velocity_score=10
        )
        self.snapshot_a = IntegrationSnapshotService.generate_snapshot(self.user_a)
        
        self.event_a = CareerOutcomeEvent.objects.create(
            user=self.user_a,
            event_type=CanonicalOutcomeEvent.SKILL_VERIFIED,
            source_domain=DomainName.EVIDENCE,
            payload={"skill": "React"}
        )

    def test_authentication_and_authorization(self):
        # Unauthenticated
        res = self.unauth_client.get('/api/career-integration/state/current/')
        self.assertEqual(res.status_code, 401)
        
        res = self.unauth_client.get('/api/career-integration/snapshot/')
        self.assertEqual(res.status_code, 401)
        
        res = self.unauth_client.get('/api/career-integration/events/')
        self.assertEqual(res.status_code, 401)

    def test_cross_user_security(self):
        # User B attempts to read User A's snapshot
        res = self.client_b.get(f'/api/career-integration/snapshot/{self.snapshot_a.id}/')
        self.assertEqual(res.status_code, 404)
        
        # User B attempts to read User A's events
        res = self.client_b.get(f'/api/career-integration/events/{self.event_a.id}/')
        self.assertEqual(res.status_code, 404)

    def test_client_authority_attack(self):
        # Attempt to patch operating state via API
        res = self.client_a.patch('/api/career-integration/state/current/', {
            "overall_readiness_score": 100,
            "overall_health": "HEALTHY"
        })
        self.assertEqual(res.status_code, 405) # Viewset is ReadOnlyModelViewSet
        
        self.state_a.refresh_from_db()
        self.assertEqual(self.state_a.overall_readiness_score, 50)

    def test_snapshot_immutability_attack(self):
        # Attempt to patch historical snapshot
        res = self.client_a.patch(f'/api/career-integration/snapshot/{self.snapshot_a.id}/', {
            "trust_level_map": {"candidate_facts": "HYPOTHETICAL"}
        }, format='json')
        self.assertEqual(res.status_code, 405)

    def test_hypothetical_data_firewall(self):
        # Ensure snapshot explicitly marks hypothetical pathways
        self.assertEqual(self.snapshot_a.trust_level_map['career_pathways'], DataTrustLevel.HYPOTHETICAL)
        self.assertEqual(self.snapshot_a.trust_level_map['candidate_facts'], DataTrustLevel.VERIFIED)

    def test_event_replay_attack_and_reconciliation_idempotency(self):
        # Reconcile event A multiple times
        r1 = CareerReconciliationService.process_outcome_event(self.event_a)
        r2 = CareerReconciliationService.process_outcome_event(self.event_a)
        r3 = CareerReconciliationService.process_outcome_event(self.event_a)
        
        # Must return the exact same reconciliation record ID
        self.assertEqual(r1.id, r2.id)
        self.assertEqual(r2.id, r3.id)

    def test_staleness_engine(self):
        # When skill verified, downstream domains must be marked stale
        r = CareerReconciliationService.process_outcome_event(self.event_a)
        self.assertIn(DomainName.SKILL_GAP, r.domains_marked_stale)
        self.assertIn(DomainName.DECISION, r.domains_marked_stale)
        self.assertIn(DomainName.EXECUTION, r.domains_marked_stale)
        
        self.state_a.refresh_from_db()
        stale_domains = self.state_a.domains.filter(status=DomainStateStatus.STALE).values_list('domain_name', flat=True)
        self.assertIn(DomainName.SKILL_GAP, stale_domains)
        self.assertIn(DomainName.DECISION, stale_domains)

    def test_outcome_event_authority(self):
        # Ensure client cannot POST arbitrary outcome events
        res = self.client_a.post('/api/career-integration/events/', {
            "event_type": "APPLICATION_OFFER",
            "source_domain": "ANALYTICS"
        })
        self.assertEqual(res.status_code, 405)
