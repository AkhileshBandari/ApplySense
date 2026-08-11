import json
from ai_engine.fallback_manager import AIFallbackManager
from .intent_service import IntentRouterService
from .context_builder import CopilotContextBuilder
from copilot.models import ChatMessage

class ConversationService:
    def __init__(self):
        self.ai = AIFallbackManager()
        self.intent_router = IntentRouterService()

    def process_message(self, thread, user_message: str):
        """
        Processes a user message:
        1. Saves the user message.
        2. Determines intent.
        3. Builds context.
        4. Calls LLM with strict evidence-based system prompt.
        5. Parses response and saves Assistant message.
        """
        # Save User Message
        user_msg = ChatMessage.objects.create(
            thread=thread,
            role='USER',
            content=user_message
        )

        # Get recent context (last 5 messages excluding the new one)
        recent_messages = list(thread.messages.order_by('-created_at')[1:6])
        recent_messages.reverse()
        
        # Determine Intent
        # We pass the last intent if available to help routing
        last_intent = None
        for m in reversed(recent_messages):
            if m.intent and m.intent != 'UNKNOWN':
                last_intent = m.intent
                break

        intent = self.intent_router.determine_intent(user_message, current_intent=last_intent)

        # Build Context
        context_builder = CopilotContextBuilder(thread.user)
        context_data = context_builder.build_context(thread, intent)

        # Generate Response
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_message, recent_messages, context_data)

        try:
            ai_response = self.ai.generate_content(
                system_prompt,
                user_prompt,
                response_format_json=True
            )
            parsed = self._parse_json(ai_response)
            
            # Save Assistant Message
            assistant_msg = ChatMessage.objects.create(
                thread=thread,
                role='ASSISTANT',
                content=parsed.get("message", "I'm sorry, I couldn't generate a clear response."),
                intent=intent,
                evidence=parsed.get("evidence", []),
                recommendations=parsed.get("recommendations", []),
                warnings=parsed.get("warnings", []),
                context_used=list(context_data.keys()),
                model_provider="AIFallbackManager",
                error_state=""
            )
            
            thread.last_message_at = assistant_msg.created_at
            thread.save()
            return assistant_msg
            
        except Exception as e:
            error_msg = ChatMessage.objects.create(
                thread=thread,
                role='ASSISTANT',
                content="The AI provider is currently unavailable or returned an error. Please try again later.",
                error_state=str(e)
            )
            return error_msg

    def _build_system_prompt(self):
        return """You are the ApplySense AI Career Copilot.
Your strict rules are:
1. ONLY provide advice based on the provided VERIFIED FACTUAL CONTEXT.
2. NEVER invent, fabricate, or hallucinate skills, metrics, jobs, or experiences.
3. NEVER guarantee a hiring outcome (e.g., "You will get this job").
4. NEVER invent a match score; use the provided JobMatch score if available.
5. If the user asks about analytics or why they are failing, rely ONLY on the provided Analytics Context.
6. Clearly separate facts, observations, and recommendations.
7. Return your response as a strictly valid JSON object matching this schema:
{
  "message": "Your main textual response to the user. Use markdown.",
  "evidence": [{"type": "JOB_MATCH", "label": "Match Score", "value": 82}],
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "warnings": ["Insufficient data to determine outcome"]
}
"""

    def _build_user_prompt(self, current_message: str, history: list, context_data: dict):
        history_text = "\n".join([f"{m.role}: {m.content}" for m in history])
        context_json = json.dumps(context_data, indent=2)
        
        return f"""[VERIFIED FACTUAL CONTEXT]
{context_json}

[CONVERSATION HISTORY]
{history_text}

[NEW USER MESSAGE]
{current_message}

Process this message according to your system rules and output JSON.
"""

    def _parse_json(self, response_text: str) -> dict:
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except Exception:
            return {"message": response_text}
