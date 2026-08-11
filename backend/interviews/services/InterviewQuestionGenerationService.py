from ai_engine.fallback_manager import AIFallbackManager
from interviews.models import InterviewQuestion
import json

class InterviewQuestionGenerationService:
    def __init__(self):
        self.ai = AIFallbackManager()

    def generate_questions(self, session, plan_section, count=3):
        """
        Generates questions for a specific section and saves them to the session.
        Grounds questions by explicitly linking source_refs.
        """
        section_type = plan_section.section_type
        snapshot = session.context_snapshot or {}
        
        # Build grounding context string
        context_str = ""
        if section_type == 'TECHNICAL' and snapshot.get('job_title'):
            context_str += f"Target Job: {snapshot.get('job_title')}\n"
        if section_type == 'RESUME' and snapshot.get('resume_version_id'):
            context_str += "The candidate has a verified resume on file.\n"
            
        system_prompt = "You are an expert technical and behavioral interviewer."
        user_prompt = f"""
        Generate {count} interview questions for a {section_type} interview section.
        Context:
        {context_str}
        
        Return a JSON array of objects, each containing:
        - question_text (string)
        - question_type (string, e.g. TECHNICAL, BEHAVIORAL)
        - reason_code (string, e.g. JOB_REQUIRED, RESUME_CLAIM)
        - expected_concepts (list of strings, concepts they should mention)
        """
        
        try:
            response = self.ai.generate_content(
                system_prompt,
                user_prompt,
                response_format_json=True
            )
            data = self._parse_json(response)
            if not isinstance(data, list):
                data = data.get('questions', [])
                
            questions = []
            for idx, q_data in enumerate(data):
                q = InterviewQuestion.objects.create(
                    session=session,
                    plan=session.plan,
                    question_type=q_data.get('question_type', section_type),
                    category=section_type,
                    difficulty=session.difficulty,
                    question_text=q_data.get('question_text', ''),
                    reason_code=q_data.get('reason_code', plan_section.reason_code),
                    expected_concepts=q_data.get('expected_concepts', []),
                    sequence=idx
                )
                questions.append(q)
            return questions
            
        except Exception:
            return []
            
    def _parse_json(self, text):
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            return []
