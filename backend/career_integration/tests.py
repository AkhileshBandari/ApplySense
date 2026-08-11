from django.test import TestCase
from django.contrib.auth import get_user_model
from career_integration.models import (
    CareerOperatingState, CareerIntegrationSnapshot, CareerOutcomeEvent, CanonicalOutcomeEvent, DomainName, DomainStateStatus
)
from career_integration.services.reconciliation_service import CareerReconciliationService
from career_integration.services.snapshot_service import IntegrationSnapshotService

User = get_user_model()

class CareerIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")

    def test_snapshot_generation(self):
        snapshot = IntegrationSnapshotService.generate_snapshot(self.user)
        self.assertIsNotNone(snapshot.snapshot_hash)
        self.assertEqual(snapshot.trust_level_map['career_pathways'], 'HYPOTHETICAL')
        self.assertEqual(snapshot.trust_level_map['candidate_facts'], 'VERIFIED')

    def test_reconciliation_service_marks_stale(self):
        # Fire an event
        event = CareerOutcomeEvent.objects.create(
            user=self.user,
            event_type=CanonicalOutcomeEvent.SKILL_VERIFIED,
            source_domain=DomainName.EVIDENCE,
            payload={"skill": "Python"}
        )
        
        record = CareerReconciliationService.process_outcome_event(event)
        self.assertIn(DomainName.SKILL_GAP, record.domains_marked_stale)
        self.assertIn(DomainName.DECISION, record.domains_marked_stale)
        
        # Verify operating state was updated
        operating_state = CareerOperatingState.objects.get(user=self.user)
        skill_gap_domain = operating_state.domains.get(domain_name=DomainName.SKILL_GAP)
        self.assertEqual(skill_gap_domain.status, DomainStateStatus.STALE)

    def test_idempotent_reconciliation(self):
        event = CareerOutcomeEvent.objects.create(
            user=self.user,
            event_type=CanonicalOutcomeEvent.APPLICATION_SUBMITTED,
            source_domain=DomainName.EXECUTION,
            payload={"job_id": 123}
        )
        
        record1 = CareerReconciliationService.process_outcome_event(event)
        record2 = CareerReconciliationService.process_outcome_event(event)
        
        self.assertEqual(record1.id, record2.id)

    def test_api_endpoints_are_protected(self):
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.get('/api/career-integration/state/current/')
        self.assertEqual(response.status_code, 401)
        
        client.force_authenticate(user=self.user)
        response = client.get('/api/career-integration/state/current/')
        self.assertEqual(response.status_code, 200)
