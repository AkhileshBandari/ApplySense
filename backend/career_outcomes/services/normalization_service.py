from career_outcomes.models import NormalizedOutcomeState

class OutcomeNormalizationService:
    """
    Deterministic normalization service mapping raw lifecycle states into canonical outcomes.
    Never invents mappings where confidence is insufficient.
    """
    
    EXACT_MAP = {
        "applied": NormalizedOutcomeState.APPLIED,
        "submitted": NormalizedOutcomeState.SUBMITTED,
        "application viewed": NormalizedOutcomeState.SCREENING,
        "employer contacted you": NormalizedOutcomeState.SCREENING,
        "interview": NormalizedOutcomeState.INTERVIEW,
        "phone screen": NormalizedOutcomeState.INTERVIEW,
        "technical interview": NormalizedOutcomeState.INTERVIEW,
        "final round": NormalizedOutcomeState.FINAL_ROUND,
        "offer": NormalizedOutcomeState.OFFER,
        "accepted": NormalizedOutcomeState.ACCEPTED,
        "rejected": NormalizedOutcomeState.REJECTED,
        "withdrawn": NormalizedOutcomeState.WITHDRAWN,
        "no response": NormalizedOutcomeState.NO_RESPONSE
    }

    @classmethod
    def normalize(cls, raw_state: str) -> str:
        if not raw_state:
            return NormalizedOutcomeState.UNKNOWN
        
        lower_state = raw_state.strip().lower()
        if lower_state in cls.EXACT_MAP:
            return cls.EXACT_MAP[lower_state]
            
        # Add basic partial match safeties where deterministic
        if "rejected" in lower_state:
            return NormalizedOutcomeState.REJECTED
        if "offer extended" in lower_state or "offer received" in lower_state:
            return NormalizedOutcomeState.OFFER
            
        return NormalizedOutcomeState.UNKNOWN
