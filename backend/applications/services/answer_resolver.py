from profiles.services.candidate_context import CandidateContextService
from applications.models import ApplicationAnswerMemory

class ApplicationAnswerResolver:
    """
    Deterministically resolves answers for application questions without AI hallucination.
    """
    
    # Sensitive categories that MUST require user input unless explicitly saved in memory with consent
    SENSITIVE_CATEGORIES = {
        'DEMOGRAPHIC_OPTIONAL',
        'CONSENT',
    }

    @staticmethod
    def normalize_question_key(question_text: str) -> str:
        """
        Normalizes phrasing to a canonical key.
        e.g., "Will you require visa sponsorship?" -> "SPONSORSHIP_REQUIRED"
        """
        text = question_text.lower()
        if 'sponsorship' in text and ('require' in text or 'need' in text):
            return 'SPONSORSHIP_REQUIRED'
        if 'notice period' in text:
            return 'NOTICE_PERIOD'
        if 'salary expectation' in text or 'expected ctc' in text:
            return 'SALARY_EXPECTATION'
        if 'authorized to work' in text or 'right to work' in text:
            return 'WORK_AUTHORIZATION'
        if 'portfolio' in text and 'url' in text:
            return 'PORTFOLIO_URL'
        if 'github' in text:
            return 'GITHUB_URL'
        if 'linkedin' in text:
            return 'LINKEDIN_URL'
        if 'gender' in text or 'race' in text or 'veteran' in text or 'disability' in text:
            return 'DEMOGRAPHIC_OPTIONAL'
        if 'terms and conditions' in text or 'consent' in text or 'acknowledge' in text:
            return 'CONSENT'
        
        # Fallback to a safe hash or the text itself if not recognized
        return text.strip()[:100]

    @staticmethod
    def resolve(user, question_text: str, question_category: str = None) -> dict:
        """
        Resolves the answer based on verified context or memory.
        Returns: { 'answer': str, 'source': str, 'review_status': str }
        """
        question_key = ApplicationAnswerResolver.normalize_question_key(question_text)
        category = question_category or 'CUSTOM'
        
        # 1. Block sensitive questions natively
        if question_key in ApplicationAnswerResolver.SENSITIVE_CATEGORIES or category in ApplicationAnswerResolver.SENSITIVE_CATEGORIES:
            memory = ApplicationAnswerMemory.objects.filter(user=user, question_key=question_key).first()
            if memory and memory.verification_status == 'VERIFIED':
                return {
                    'answer': memory.answer,
                    'source': 'ANSWER_MEMORY',
                    'review_status': 'REVIEW_RECOMMENDED'
                }
            return {
                'answer': None,
                'source': 'UNANSWERED',
                'review_status': 'USER_INPUT_REQUIRED',
                'reason': 'Sensitive or consent questions require explicit user input.'
            }

        # 2. Check Candidate Context (Verified Data)
        context = CandidateContextService.get_for_user(user)
        
        # We explicitly map keys to context fields
        context_mapping = {
            'LINKEDIN_URL': ('contact', 'linkedin'),
            'GITHUB_URL': ('contact', 'github'),
            'PORTFOLIO_URL': ('contact', 'portfolio'),
        }
        
        if question_key in context_mapping:
            group, field = context_mapping[question_key]
            val = context.get(group, {}).get(field)
            if val:
                return {'answer': val, 'source': 'VERIFIED_PROFILE', 'review_status': 'AUTO_RESOLVED'}
                
        # 3. Check Answer Memory
        memory = ApplicationAnswerMemory.objects.filter(user=user, question_key=question_key).first()
        if memory:
            return {
                'answer': memory.answer,
                'source': 'ANSWER_MEMORY',
                'review_status': 'AUTO_RESOLVED' if memory.verification_status == 'VERIFIED' else 'REVIEW_RECOMMENDED'
            }

        # 4. Fail Closed -> User Input Required
        return {
            'answer': None,
            'source': 'UNANSWERED',
            'review_status': 'USER_INPUT_REQUIRED',
            'reason': 'No verified evidence or saved memory found.'
        }
