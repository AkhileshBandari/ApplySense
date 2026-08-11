import logging
from ai_engine.fallback_manager import AIFallbackManager

logger = logging.getLogger(__name__)

CLAIM_VALIDATION_PROMPT = """You are a strict compliance auditor evaluating resume modifications.
Your job is to prevent candidates from fabricating experience, inventing skills, or hallucinating metrics that are not supported by their verified career history.

You will be given:
1. CANDIDATE VERIFIED EVIDENCE: A trusted list of facts about the candidate.
2. PROPOSED CLAIM: A new bullet point or sentence proposed for their resume.

Evaluate if the PROPOSED CLAIM is supported by the EVIDENCE.
Classify the claim into ONE of the following categories:
- SUPPORTED: The proposed claim perfectly matches the evidence.
- SUPPORTED_REPHRASE: The proposed claim uses different wording but conveys the exact same factual meaning as the evidence (e.g. "Built APIs" -> "Developed APIs").
- AMBIGUOUS: The proposed claim might be true based on the evidence, but it implies something slightly broader or lacks explicit proof in the evidence (e.g. "Wrote tests" -> "Led testing strategies").
- UNSUPPORTED: The proposed claim invents new metrics, new skills, new responsibilities, or new roles not found in the evidence. (e.g. "Improved performance" -> "Improved performance by 40%").

Respond with ONLY the classification string (SUPPORTED, SUPPORTED_REPHRASE, AMBIGUOUS, or UNSUPPORTED). Do not provide any explanation.
"""

class ClaimValidationService:
    @staticmethod
    def validate_claim(verified_evidence_text: str, proposed_claim: str) -> str:
        """
        Validate a proposed resume claim against verified candidate evidence.
        Returns: SUPPORTED, SUPPORTED_REPHRASE, AMBIGUOUS, or UNSUPPORTED.
        """
        ai = AIFallbackManager()
        
        try:
            response = ai.generate_content(
                system_prompt=CLAIM_VALIDATION_PROMPT,
                user_prompt=f"CANDIDATE VERIFIED EVIDENCE:\n{verified_evidence_text}\n\nPROPOSED CLAIM:\n{proposed_claim}",
                response_format_json=False
            )
            
            cleaned = response.strip().upper()
            
            # Extract the actual valid status if the LLM gets chatty
            for status in ['SUPPORTED_REPHRASE', 'UNSUPPORTED', 'AMBIGUOUS', 'SUPPORTED']:
                if status in cleaned:
                    return status
            
            # Default to UNSUPPORTED if we can't parse it securely
            logger.warning(f"Failed to parse claim validation response: {cleaned}")
            return "UNSUPPORTED"
            
        except Exception as e:
            logger.error(f"Claim validation failed: {str(e)}")
            # Fail closed (safe)
            return "UNSUPPORTED"
