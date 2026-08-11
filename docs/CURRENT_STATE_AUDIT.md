# ApplySense - Forensic Audit & Current State Report

## 1. Verified Current Completion: ~10% (Not 20%)

The previous estimate of 20% was overly generous. While basic database models, a React scaffold, and Python API views exist, true end-to-end functionality for most of the core loops is either mocked, stubbed, or missing entirely. 

The codebase represents a **scaffolded prototype**, heavily reliant on client-side mocks and permissive backend error suppression. It is an excellent starting point, but significant architectural connections are missing.

## 2. What Already Works
- **Database Architecture:** `Profile`, `Job`, `Resume`, `Application`, and `Interview` models are cleanly defined in Django (`backend/profiles/models.py`, `backend/jobs/models.py`, etc.).
- **Frontend Skeleton:** A React/Vite setup with Tailwind CSS exists, containing basic routing and structural pages (`DashboardPage`, `ApplicationsPage`, `ProfilePage`, `CoachPage`, `ResumesPage`).
- **Prompt Infrastructure:** `backend/ai_engine/prompts.py` has well-structured system prompts for Resume Parsing, Skill Gaps, Roadmaps, and Interview Prep.
- **Basic Job Matcher:** `backend/jobs/matcher.py` provides a baseline heuristic scoring system (comparing required years of experience vs. candidate experience).

## 3. What is Partially Implemented
- **AI Services (`career_ops` and `ai_engine`):** Functions exist to call LLMs via `AIFallbackManager`. However, real provider integrations are mostly stubbed with `NotImplementedError` in `fallback_manager.py`.
- **Browser Extension:** `extension/content.js` can scrape rudimentary text elements from Greenhouse, Lever, Ashby, and LinkedIn, but lacks form-filling logic.
- **Electron Desktop App:** Basic `main.js` boilerplate exists, but contains no desktop-specific functionality.

## 4. What is Mocked
- **Frontend State & Dashboards:** Pages like `ProfilePage.tsx` and `DashboardPage.tsx` rely heavily on `frontend/src/utils/mockData.ts`. If the backend is unreachable, the UI gracefully downgrades to high-fidelity mock data rather than showing errors.
- **AI Fallbacks:** In `backend/ai_engine/views.py`, if an LLM fails, broad `except Exception:` blocks suppress the error and return hardcoded fallback dictionaries (e.g., hardcoded behavioral questions).

## 5. What is Broken
- **Test Coverage:** Non-existent. Directory queries for `backend/tests` and `frontend/tests` return nothing. The inline `tests.py` files in Django apps are essentially empty boilerplate.
- **Job Ingestion Engine:** `backend/automation/scrapers.py` contains placeholders (e.g., `# Placeholder – real implementation would parse lists`) and cannot handle robust real-world job postings at scale.

## 6. What is Completely Missing
- **Tsenta-style Auto-Apply Engine:** There is no code to map structured candidate data to DOM elements or submit applications automatically.
- **Application Question Memory:** No models exist to remember standard user answers (e.g., visa status, salary expectations, notice period).
- **Resume Tailoring Generation:** `career_ops/tailoring.py` generates a text summary but lacks a mechanism to dynamically reconstruct and export a tailored PDF/Docx.
- **Authentication Flow:** While Django has auth tables, the React frontend lacks a fully wired JWT/OAuth session management system.
- **Analytics Engine:** The charts in `DashboardPage.tsx` use predefined structures. There is no SQL aggregation logic to calculate actual rejection or offer rates over time.

## 7. Critical Architecture Issues
- **Permissive Error Handling:** Broad exception catching in the backend AI services masks failures and prevents debugging. 
- **Monolithic React Pages:** React code is heavily concentrated into massive `Page.tsx` files rather than modular, reusable components in `src/components/`.

## 8. Critical Security Issues
- **Missing Object-Level Permissions:** Deep validation of object ownership (e.g., ensuring User A cannot retrieve or modify User B's resumes or applications) needs rigorous verification across all API endpoints.

---

## 9. Requirement Traceability Matrix (Master Context Mapping)

| Section | Feature | Status | Evidence/File Paths | What Must Be Done |
|---|---|---|---|---|
| 4 | AI Career Profile | PARTIAL | `profiles/models.py`, `ProfilePage.tsx` | Add fields for GitHub, Portfolio, work auth. Wire UI to API reliably. |
| 5 | AI Career Copilot | MOCKED | `CoachPage.tsx`, `ai_engine/views.py` | Implement conversation history DB models. Replace hardcoded AI fallback strings. |
| 6 | Resume Intelligence | PARTIAL | `resumes/models.py`, `ai_engine/views.py` | Build structured JSON parsing logic. Build a true ATS rule evaluator. |
| 7 | Job-Specific Resume Tailoring | PARTIAL | `career_ops/tailoring.py` | Create a PDF/Docx generation engine. Ensure zero hallucination rules. |
| 8 | Job Discovery Engine | SCAFFOLDED | `automation/scrapers.py`, `content.js` | Build background Celery workers for ingestion. Build deduplication logic. |
| 9 | AI Job Matching Engine | PARTIAL | `jobs/matcher.py` | Upgrade from basic keyword counting to semantic vector matching. |
| 10 | Smart Job Feed | MOCKED | `DashboardPage.tsx`, `mockData.ts` | Build filtering APIs (remote, experience, match score). |
| 11 | Tsenta-style Auto-Apply | MISSING | N/A | Build extension form-filling and submission orchestration logic. |
| 12 | Application Safety Layer | MISSING | N/A | Create models for user-defined application limits and constraints. |
| 13 | Application Question Memory | MISSING | N/A | Create models to save answers to standard ATS questions. |
| 14 | Application Tracker | PARTIAL | `applications/models.py`, `ApplicationsPage.tsx` | Wire UI completely to backend. Add stage transition logic. |
| 15 | Job Search Analytics | MOCKED | `DashboardPage.tsx` (Charts) | Build SQL aggregation logic for offer rates, rejection rates. |
| 16 | Skill Gap Analysis | PARTIAL | `ai_engine/views.py` (SkillGapAnalysisView) | Connect explicitly to user profile skills vs job requirements. |
| 17 | Personalized Learning Roadmap | PARTIAL | `ai_engine/views.py` (LearningRoadmapView) | Store generated roadmaps in DB to track progress over time. |
| 18 | Project Recommendation | MISSING | N/A | Build AI logic to suggest portfolio projects based on skill gaps. |
| 19 | GitHub Analysis | MISSING | N/A | Integrate GitHub API to evaluate commit activity and repos. |
| 20 | Portfolio Analysis | MISSING | N/A | Build scraper/evaluator for candidate portfolio URLs. |
| 21 | LinkedIn Optimization | MISSING | N/A | Build LinkedIn profile scoring evaluator. |
| 22 | AI Interview Prep | PARTIAL | `ai_engine/views.py` (InterviewPrepView) | Generate context-aware questions based on specific job descriptions. |
| 23 | AI Mock Interview | MISSING | N/A | Build real-time conversational agent interface with voice/text. |
| 24-27 | Specialized Interview/Analytics| MISSING | N/A | Build logic for coding prep, company prep, AI recruiter sim. |
