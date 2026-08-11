import hashlib
import json
from career_integration.models import (
    CareerOperatingState, CareerDomainState, CareerIntegrationSnapshot, DataTrustLevel, DomainName
)

class IntegrationSnapshotService:
    @staticmethod
    def generate_snapshot(user) -> CareerIntegrationSnapshot:
        """
        Creates a point-in-time deterministic snapshot of the candidate's holistic state.
        Never flattens trust boundaries. Explicitly labels what is verified vs derived vs hypothetical.
        """
        # In a real system, these would fetch from ContextService, AnalyticsService, etc.
        # We will stub the payload structure representing authoritative read-only mapping.
        
        payload = {
            "candidate_facts": {
                "skills_verified": 10,
                "work_authorization": "US",
            },
            "analytics": {
                "applications_submitted": 25,
                "interview_rate_pct": 12
            },
            "career_decision": {
                "current_priority": "Backend Engineering",
                "top_blocker": "System Design Experience"
            },
            "career_execution": {
                "active_tasks": 4,
                "progress_score": 65
            },
            "career_pathways": {
                "active_scenario": "Switch to MLE",
                "scenario_assumptions": ["Learn PyTorch"]
            }
        }
        
        trust_level_map = {
            "candidate_facts": DataTrustLevel.VERIFIED,
            "analytics": DataTrustLevel.DERIVED,
            "career_decision": DataTrustLevel.ADVISORY,
            "career_execution": DataTrustLevel.VERIFIED,
            "career_pathways": DataTrustLevel.HYPOTHETICAL
        }
        
        payload_str = json.dumps(payload, sort_keys=True)
        snapshot_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        snapshot = CareerIntegrationSnapshot.objects.create(
            user=user,
            payload=payload,
            snapshot_hash=snapshot_hash,
            trust_level_map=trust_level_map
        )
        
        return snapshot
