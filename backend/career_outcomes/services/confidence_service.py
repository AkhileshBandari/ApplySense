from career_outcomes.models import OutcomeConfidence

class ConfidenceService:
    """
    Deterministic confidence classification for outcome analytics.
    """
    
    @classmethod
    def calculate_confidence(cls, sample_size: int, comparison_size: int = None) -> str:
        # If it's a comparative analysis, use the minimum of the two groups
        n = min(sample_size, comparison_size) if comparison_size is not None else sample_size
        
        if n < 5:
            return OutcomeConfidence.VERY_LOW
        if n < 15:
            return OutcomeConfidence.LOW
        if n < 50:
            return OutcomeConfidence.MEDIUM
        if n < 150:
            return OutcomeConfidence.HIGH
            
        return OutcomeConfidence.VERY_HIGH
