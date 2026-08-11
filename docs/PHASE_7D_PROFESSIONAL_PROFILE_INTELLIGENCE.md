# Phase 7D: Professional Profile Intelligence & Career Brand Optimization

## Overview
Phase 7D introduces the `career_brand` Django application. Its purpose is to ingest external professional profiles (e.g., LinkedIn exports, manual text, or future API integrations), analyze them against verified truths in the system, and provide actionable recommendations to improve the candidate's career brand (Recruiter Readiness, Keyword Coverage, etc.).

## Core Principles & Trust Boundaries
1. **Profile Data is a Claim, NOT Truth**: Any text imported or typed into a Professional Profile is treated as a claim. It does not update the user's `CandidateContext` unless explicitly pushed through the core verification pipeline.
2. **Deterministic Scoring**: Scores like `completeness_score` and `recruiter_readiness_score` are strictly deterministic. They are built from the presence of fields and the mathematical classification of their claims.
3. **Prompt-Injection Defense**: AI is only used to *propose* text (e.g., rewriting a headline). All generated text is subsequently run through the deterministic `ClaimValidationService` to prevent hallucinated achievements or unverified skills from leaking into the profile.
4. **Provider-Neutrality**: The system is built generically. It does not enforce a LinkedIn-specific schema and relies on structured models like `ProfessionalProfileSection` to adapt to various data sources.

## Architecture

### Models
- `ProfessionalProfile`: The canonical record holding headline, about, location, and metadata.
- `ProfessionalProfileSection`: Holds individual sections (Experience, Education, Skills).
- `ProfessionalProfileAnalysis`: An immutable snapshot of a specific analysis run, storing scores and the state of the system at the time.
- `ProfessionalProfileRecommendation`: Actionable items (e.g., `MISSING_ABOUT`, `UNSUPPORTED_PROFILE_CLAIM`) generated during analysis.
- `ProfessionalProfileVersion`: The final, user-approved snapshot of an optimized profile.

### Services
- **ClaimValidationService**: Compares raw profile text against the `CandidateContext` (for verified facts) and `CandidateSkillEvidence` (for Phase 7C unverified evidence). Returns classifications of `supported`, `unsupported`, or `evidence_only`.
- **ScoringEngine**: Calculates 0-100 scores for completeness and readiness.
- **ConsistencyEngine**: Detects inconsistencies between the profile and the active `ResumeVersion`.
- **ProfileOptimizationService**: Coordinates analysis and generates AI proposals for recommendations. Ensures AI proposals pass `ClaimValidationService` before presenting to the user.

### Copilot Integration
The `CopilotContextBuilder` now injects a `career_brand_context` containing the latest readiness score, completeness score, top pending recommendations, and an explicit system disclaimer preventing the AI from trusting the profile content blindly.

## API Endpoints
- `GET /api/career-brand/profiles/`
- `POST /api/career-brand/profiles/`
- `POST /api/career-brand/profiles/{id}/analyze/`
- `GET /api/career-brand/analyses/`
- `POST /api/career-brand/recommendations/{id}/generate/`
- `POST /api/career-brand/recommendations/{id}/accept/`
- `POST /api/career-brand/recommendations/{id}/edit/`
- `POST /api/career-brand/profiles/{id}/approve_version/`

## Known Limitations
- Due to strict LinkedIn API limitations, automatic fetching of public LinkedIn URLs is not implemented. The current system relies on manual text entry or copy/paste formats.
- The `ConsistencyEngine` currently performs a basic title check and requires NLP extensions for deeper semantic comparisons.
