# Phase 2: Candidate Intelligence & Verified Profiles

## Overview

Phase 2 builds upon the strong authentication and authorization foundation of Phase 1 by implementing a robust, AI-powered Candidate Intelligence layer. This phase introduces deep resume parsing, structured candidate data models, and a secure fact-verification process.

## Key Features

1. **Enhanced Data Models with Provenance**
   - Introduced models: `Project`, `Language`, `CareerPreferences`, `WorkAuthorization`.
   - Added `ProvenanceMixin` to all profile entities (`Experience`, `Education`, `Skill`, etc.) to track their `source` (e.g., User Input, Resume Extracted) and `verification_status` (UNVERIFIED, VERIFIED, REJECTED).
   - Ensured that AI-extracted data does not automatically pollute the user's verified profile.

2. **Resume Parsing Lifecycle**
   - Resumes now track their processing lifecycle: `UPLOADED` -> `EXTRACTING` -> `PARSING` -> `REVIEW_REQUIRED` -> `CONFIRMED` / `FAILED`.
   - **Extraction Service**: Extracts raw text from PDFs and DOCX files.
   - **Parsing Service**: Invokes the verified `AIFallbackManager` to structure the raw text into JSON.
   - **Provenance Service**: Converts the structured JSON into `UNVERIFIED` records linked to the user's profile and the source resume.

3. **Frontend Integrations**
   - **Profile Completeness**: A deterministic completeness score encourages users to provide essential career information.
   - **Fact Review Mechanism**: Users can review, accept, edit, or reject AI-extracted facts via the `PendingImports` UI component on the Profile page before they are merged into their verified profile.
   - **Resumes Dashboard**: Users can track the status of their uploaded resumes and see clear feedback on parsing success or required actions.

## Security and Verification Constraints

- **Isolation**: All new endpoints adhere to the Phase 1 tenant isolation rules, ensuring users can only interact with their own data.
- **Graceful Failures**: Errors during text extraction or AI parsing result in clear, actionable states (`FAILED`) without crashing the application or saving fake data.
- **Strict Verification**: AI output is explicitly designated as `UNVERIFIED` and requires explicit user consent (via the `MergeService`) to become `VERIFIED`.

## Verification Status

**Status: VERIFIED (PASS)**

An adversarial verification was completed covering 32 failure and security cases.
- Tests confirm object-level isolation.
- Extracted facts default safely to `UNVERIFIED` and cannot pollute the Profile without user action.
- Build and Backend suites execute successfully (28/28 tests passing).
- Production blockers and mock technical debt were resolved.

## Next Steps

With a verified and structured career profile, ApplySense is ready for Phase 3: Opportunity Discovery and AI Auto-Tailoring.
