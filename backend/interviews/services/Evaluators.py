from ai_engine.fallback_manager import AIFallbackManager
import json

class BaseEvaluator:
    def __init__(self):
        self.ai = AIFallbackManager()

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

class STARResponseEvaluator(BaseEvaluator):
    def evaluate(self, response_obj):
        """
        Evaluate behavioral responses using the STAR method.
        Splits deterministic structural scoring from semantic feedback.
        """
        question_text = response_obj.question.question_text
        answer = response_obj.response_text
        
        system_prompt = "You are an expert behavioral interviewer evaluating an answer using the STAR method (Situation, Task, Action, Result)."
        user_prompt = f"""
        Question: {question_text}
        Candidate Answer:
        [START ANSWER]
        {answer}
        [END ANSWER]
        
        Evaluate the candidate's answer.
        Does it contain a clear Situation? (bool)
        Does it contain a clear Task? (bool)
        Does it contain a clear Action? (bool)
        Does it contain a clear Result? (bool)
        
        Return a JSON object:
        {{
            "has_situation": bool,
            "has_task": bool,
            "has_action": bool,
            "has_result": bool,
            "relevance_score": int (0-100),
            "communication_score": int (0-100),
            "strengths": ["string"],
            "weaknesses": ["string"],
            "feedback": "string"
        }}
        """
        
        try:
            ai_resp = self.ai.generate_content(system_prompt, user_prompt, response_format_json=True)
            data = self._parse_json(ai_resp) or {}
            
            # Deterministic structure score
            has_s = data.get('has_situation', False)
            has_t = data.get('has_task', False)
            has_a = data.get('has_action', False)
            has_r = data.get('has_result', False)
            
            structure_score = sum([25 for x in [has_s, has_t, has_a, has_r] if x])
            
            relevance = data.get('relevance_score', 50)
            comm = data.get('communication_score', 50)
            
            overall = int((structure_score * 0.4) + (relevance * 0.4) + (comm * 0.2))
            
            return {
                'structure_score': structure_score,
                'relevance_score': relevance,
                'communication_score': comm,
                'overall_score': overall,
                'strengths': data.get('strengths', []),
                'weaknesses': data.get('weaknesses', []),
                'feedback': data.get('feedback', '')
            }
        except Exception:
            return {
                'overall_score': 0,
                'feedback': 'Evaluation failed due to AI error.'
            }


class TechnicalResponseEvaluator(BaseEvaluator):
    def evaluate(self, response_obj):
        """
        Evaluate technical responses.
        Flags unsupported claims and checks for expected concepts.
        """
        question_text = response_obj.question.question_text
        expected_concepts = response_obj.question.expected_concepts or []
        answer = response_obj.response_text
        
        system_prompt = "You are a senior staff engineer evaluating a candidate's technical interview answer."
        snapshot = response_obj.question.session.context_snapshot or {}
        verified_skills = snapshot.get('candidate_context', {}).get('verified_skills', [])
        
        user_prompt = f"""
        Question: {question_text}
        Expected Concepts: {expected_concepts}
        Candidate's Verified Skills: {verified_skills}
        
        Candidate Answer:
        [START ANSWER]
        {answer}
        [END ANSWER]
        
        Evaluate technical accuracy, completeness against expected concepts, and communication.
        Crucially, flag any skills or technologies the candidate claims to have experience with that are NOT in their 'Verified Skills' list. Output them in the 'unsupported_claims' array.
        
        Return JSON:
        {{
            "technical_accuracy_score": int (0-100),
            "completeness_score": int (0-100),
            "communication_score": int (0-100),
            "strengths": ["string"],
            "weaknesses": ["string"],
            "missing_concepts": ["string"],
            "unsupported_claims": ["string"],
            "feedback": "string"
        }}
        """
        
        try:
            ai_resp = self.ai.generate_content(system_prompt, user_prompt, response_format_json=True)
            data = self._parse_json(ai_resp) or {}
            
            tech = data.get('technical_accuracy_score', 50)
            comp = data.get('completeness_score', 50)
            comm = data.get('communication_score', 50)
            
            overall = int((tech * 0.5) + (comp * 0.3) + (comm * 0.2))
            
            return {
                'technical_accuracy_score': tech,
                'completeness_score': comp,
                'communication_score': comm,
                'overall_score': overall,
                'strengths': data.get('strengths', []),
                'weaknesses': data.get('weaknesses', []),
                'missing_concepts': data.get('missing_concepts', []),
                'unsupported_claims': data.get('unsupported_claims', []),
                'feedback': data.get('feedback', '')
            }
        except Exception:
            return {
                'overall_score': 0,
                'feedback': 'Evaluation failed due to AI error.'
            }
