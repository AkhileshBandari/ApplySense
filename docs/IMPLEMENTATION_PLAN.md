# ApplySense - Phased Implementation Plan

**Objective:** Preserve, repair, and complete the existing prototype to achieve the Master Project Context vision. Do NOT rebuild from scratch. Extend the existing Django backend and React/Vite frontend.

## Verification Status
- **Phase 1 (Foundation & Auth):** VERIFIED PASS
- **Phase 2 (Candidate Intelligence):** VERIFIED PASS
- **Phase 3 (Resume Intelligence/Tailoring):** VERIFIED PASS
- **Phase 4 (Job Intelligence):** VERIFIED PASS
- **Phase 5A (Application Intelligence):** PARTIAL (Backend logic missing for snapshots, duplicate detection, and answer memory anti-hallucination)

## Phase 1: Foundation & Data Integrity Repair
*The goal of this phase is to replace frontend mocks with real database-backed API calls and fix the permissive AI error handling.*

1. **Authentication & Authorization:**
   - Wire `frontend/src/pages/LoginPage.tsx` to Django's authentication endpoints (JWT).
   - Ensure `ProtectedRoute.tsx` properly enforces active sessions.
   - Enforce Object-Level permissions on all backend API views to ensure data privacy.

2. **Remove Frontend Mocks:**
   - Refactor `ProfilePage.tsx`, `DashboardPage.tsx`, and `ApplicationsPage.tsx` to strictly consume `services/api.ts` data.
   - Gracefully handle API failures with user-facing errors or empty states, rather than falling back to fake data in `mockData.ts`.

3. **Backend AI Error Handling Refactor:**
   - Modify `ai_engine/views.py` and `services/career_ops/` to properly raise and log exceptions when LLM parsing fails, instead of masking them with hardcoded strings like "Fallback roadmap generated locally."
   - Implement actual provider API calls (e.g., OpenAI/Gemini) inside `AIFallbackManager` replacing the `NotImplementedError` stubs.

## Phase 2: Core Profile & Job Intelligence Completeness
*The goal of this phase is to complete the foundational intelligence layers.*

1. **Deep Resume Parsing & Verified Profiles:**
   - Expanded `ResumeParseView` to extract and save structured JSON via a formal extraction and parsing service layer.
   - Introduced `ProvenanceMixin` and a lifecycle status to `Resume` to ensure AI-extracted facts are marked as `UNVERIFIED`.
   - Created a Fact Review flow (`PendingImportView`, `FactReviewView`) on the frontend to allow users to verify extracted data before it enters their main profile.
   - Implemented a deterministic Profile Completeness calculation.

2. **Advanced Job Matching:**
   - Refactor `jobs/matcher.py` to utilize a more sophisticated semantic comparison (e.g., using lightweight embeddings via pgvector) instead of relying solely on exact text matches for predefined skills.
   - Upgrade the `JobDiscoveryEngine` and background scrapers to correctly parse structured job requirements.

## Phase 3: The Auto-Apply Engine & Application Tracker (The Tsenta Loop)
*The goal of this phase is to build the application automation pipeline.*

1. **Application Question Memory:**
   - Create a new Django model `ApplicationAnswerMemory` linked to the User profile to securely store common responses (e.g., Visa status, Salary expectations, Notice Period).

2. **Browser Extension Autofill Orchestration:**
   - Extend `extension/content.js` to map standard ATS DOM fields and securely inject data fetched from the `ApplicationAnswerMemory` API.

3. **Application Safety Layer:**
   - Create `AutomationRule` models in Django to allow users to set strict parameters (max applications per day, minimum salary, excluded companies) before the extension executes an apply action.

## Phase 4: Career Copilot & Advanced Features
*The goal of this phase is to build the conversational and learning modules.*

1. **Conversational Memory for Coach:**
   - Create `ChatThread` and `ChatMessage` models in Django.
   - Refactor `CoachPage.tsx` to support a continuous conversation history rather than isolated, stateless AI API calls.

2. **Dynamic Interview Prep:**
   - Link `InterviewPrepView` directly to a specific `Job` and `Resume` instance in the database to generate highly targeted technical and behavioral questions based on the intersection of the candidate's actual experience and the job's actual requirements.

3. **Dynamic Resume Tailoring Engine:**
   - Extend `career_ops/tailoring.py` to move beyond text summaries and actually generate downloadable PDF/Docx files tailored to the target job description. Ensure strict zero-hallucination guardrails.
