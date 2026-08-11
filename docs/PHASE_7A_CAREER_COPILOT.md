# Phase 7A: Career Copilot

## Architecture Overview
The Career Copilot replaces the mock Coach system with a dynamic, LLM-powered AI assistant that reasons over the candidate's verified career data.

### Components
1. **ChatThread & ChatMessage Models**: Enables persistent conversational memory that survives page reloads.
2. **IntentRouterService**: Intercepts the user's message and classifies it to determine the correct context payload required.
3. **CopilotContextBuilder**: A strict context aggregator. It exclusively fetches VERIFIED facts (via CandidateContextService), job matches, applications, and analytics based on the thread context.
4. **ConversationService**: The orchestrator. It manages the prompt structure, ensuring the LLM understands the rigid boundaries of factual evidence, and processes the JSON response into persistent `ChatMessage` entities containing evidence, recommendations, and warnings.

## Trust Hierarchy
The Copilot operates strictly on a read-only factual basis. It does not update the candidate's profile based on chat input. Unverified claims made in the chat remain as conversational memory.

## Security & Isolation
All API views require authentication and enforce strict ownership checks ensuring User A can never query or post to User B's threads.
