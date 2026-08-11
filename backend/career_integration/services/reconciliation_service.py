from django.db import transaction
from career_integration.models import (
    CareerOperatingState, CareerDomainState, CareerOutcomeEvent, 
    CareerReconciliationRecord, DomainName, DomainStateStatus, CanonicalOutcomeEvent
)
from career_integration.services.snapshot_service import IntegrationSnapshotService

class CareerReconciliationService:
    @staticmethod
    def process_outcome_event(event: CareerOutcomeEvent):
        """
        Idempotent reconciliation. Determines which downstream systems are now stale
        based on a consequential outcome event.
        """
        with transaction.atomic():
            # Check if already reconciled
            if hasattr(event, 'reconciliation'):
                return event.reconciliation
            
            domains_stale = []
            
            # Application outcomes invalidate analytics, decisions, and execution plans
            if event.event_type in [
                CanonicalOutcomeEvent.APPLICATION_SUBMITTED,
                CanonicalOutcomeEvent.APPLICATION_REJECTED,
                CanonicalOutcomeEvent.APPLICATION_OFFER
            ]:
                domains_stale.extend([DomainName.ANALYTICS, DomainName.DECISION, DomainName.EXECUTION])
            
            # Interview outcomes invalidate interview intelligence and career decisions
            elif event.event_type in [CanonicalOutcomeEvent.INTERVIEW_COMPLETED, CanonicalOutcomeEvent.INTERVIEW_WEAKNESS_IDENTIFIED]:
                domains_stale.extend([DomainName.INTERVIEW, DomainName.DECISION])
                
            # Skill verifications affect gap analysis, learning roadmaps, decisions, and execution
            elif event.event_type == CanonicalOutcomeEvent.SKILL_VERIFIED:
                domains_stale.extend([DomainName.SKILL_GAP, DomainName.LEARNING, DomainName.DECISION, DomainName.EXECUTION])
            
            # Ensure unique
            domains_stale = list(set(domains_stale))
            
            # Mark domains stale
            operating_state, _ = CareerOperatingState.objects.get_or_create(user=event.user)
            for domain in domains_stale:
                domain_state, _ = CareerDomainState.objects.get_or_create(
                    operating_state=operating_state, 
                    domain_name=domain
                )
                domain_state.status = DomainStateStatus.STALE
                domain_state.save()
            
            # Optionally generate a new snapshot after marking things stale (to lock in the state)
            IntegrationSnapshotService.generate_snapshot(event.user)
            
            # Create reconciliation record
            record = CareerReconciliationRecord.objects.create(
                event=event,
                domains_marked_stale=domains_stale
            )
            
            return record
