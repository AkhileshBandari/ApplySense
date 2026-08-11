from ai_engine.fallback_manager import AIFallbackManager
from interviews.models import InterviewQuestion
import json

class AdaptiveFollowUpService:
    def __init__(self):
        self.ai = AIFallbackManager()
        self.MAX_FOLLOW_UP_DEPTH = 2

    def _parse_json(self, text):
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            return None

    def generate_follow_up(self, response_evaluation):
        """
        Generates a follow-up question based on evaluation weaknesses or missing concepts.
        Limits depth to MAX_FOLLOW_UP_DEPTH.
        """
        response_obj = response_evaluation.response
        parent_q = response_obj.question
        
        # Check depth
        depth = 0
        curr = parent_q
        while curr.is_follow_up and curr.parent_question:
            depth += 1
            curr = curr.parent_question
            
        if depth >= self.MAX_FOLLOW_UP_DEPTH:
            return None # Max depth reached
            
        # Only follow up if there is a reason
        missing = response_evaluation.missing_concepts or []
        unsupported = response_evaluation.unsupported_claims or []
        
        if not missing and not unsupported and response_evaluation.overall_score >= 80:
            return None # Good answer, no follow-up needed
            
        system_prompt = "You are an expert interviewer. Generate a follow up question."
        user_prompt = f"""
        Original Question: {parent_q.question_text}
        Candidate Answer: {response_obj.response_text}
        Missing Concepts: {missing}
        Unsupported Claims: {unsupported}
        
        Generate ONE follow up question to probe these missing areas or challenge the unsupported claims gently.
        
        Return JSON:
        {{
            "question_text": "string",
            "reason": "string"
        }}
        """
        
        try:
            ai_resp = self.ai.generate_content(system_prompt, user_prompt, response_format_json=True)
            data = self._parse_json(ai_resp) or {}
            
            if not data.get('question_text'):
                return None
                
            new_q = InterviewQuestion.objects.create(
                session=parent_q.session,
                plan=parent_q.plan,
                question_type=parent_q.question_type,
                category=parent_q.category,
                difficulty=parent_q.difficulty,
                question_text=data['question_text'],
                reason_code=f"FOLLOW_UP_{data.get('reason', 'PROBE')}",
                parent_question=parent_q,
                is_follow_up=True,
                sequence=parent_q.sequence + 1
            )
            return new_q
        except Exception:
            return None
