# Copilot Context Architecture

This document defines how contextual information is selected, bounded, and provided to the Career Copilot AI model during Phase 7A.

## Context Lifecycle

1. **User Message Reception**: The `ConversationService` intercepts a user message payload via the REST API.
2. **Intent Classification**: The `IntentRouterService` queries a fast LLM model strictly designed to map the message to a finite set of intent choices (e.g., `JOB_FIT`, `ANALYTICS`, `GENERAL_CAREER`).
3. **Context Construction**: The `CopilotContextBuilder` reads the classified intent, the active `ChatThread` bindings, and the authenticated user identity.
   - It fetches `verified_candidate_facts`.
   - It fetches `analytics_context` (KPIs, funnels) if the intent warrants it.
   - It fetches targeted `job_context` or `application_context` if the thread is specifically scoped.
4. **LLM Generation**: The aggregated context is transformed into JSON and injected into the user prompt payload beneath a rigid system prompt that strictly bounds the model's behavior.
5. **Response Parsing**: The structured JSON response is unpacked, evaluated for validity, and stored safely in the database with explicit metadata attributes indicating the specific `context_used`.
