# PHASE 7B IMPLEMENTATION AUDIT

## Goal
To audit the existing ApplySense codebase before implementing the Skill Gap Intelligence, Personalized Learning Roadmap, and Project Recommendation engines.

## 1. Domain Models

| Entity | Status | Location / Details | Action Required |
| --- | --- | --- | --- |
| `Skill` | EXISTING | `profiles.models.Skill` (User's skills with verification status) | MUST MODIFY (Extend taxonomy/canonical_name capabilities) |
| `CandidateContextService` | EXISTING | `profiles.services.candidate_context.CandidateContextService` | REUSABLE |
| `Job` | EXISTING | `jobs.models.Job` | REUSABLE |
| `JobRequirement` | EXISTING | `jobs.models.JobRequirement` | REUSABLE |
| `JobMatch` | EXISTING | `jobs.models.JobMatch` | REUSABLE |
| `Project` (Candidate) | EXISTING | `profiles.models.Project` | REUSABLE (Candidate's existing projects) |
| `Certification` | EXISTING | `profiles.models.Certification` | REUSABLE |
| `Experience` | EXISTING | `profiles.models.Experience` | REUSABLE |
| `Resume` / `ResumeVersion` | EXISTING | `resumes.models.*` | REUSABLE |
| `ChatThread` / `ChatMessage` | EXISTING | `copilot.models.*` | REUSABLE |
| `SkillGapAnalysis` | MISSING | N/A | MUST CREATE |
| `SkillGapItem` | MISSING | N/A | MUST CREATE |
| `LearningRoadmap` | MISSING | N/A | MUST CREATE |
| `LearningRoadmapItem` | MISSING | N/A | MUST CREATE |
| `LearningResource` | MISSING | N/A | MUST CREATE |
| `ProjectRecommendation` | MISSING | N/A | MUST CREATE |

## 2. Services & Architecture

| Service/Engine | Status | Details | Action Required |
| --- | --- | --- | --- |
| `HybridMatcherService` | EXISTING | `jobs.services.hybrid_matcher.py` | REUSABLE |
| `ClaimValidationService` | EXISTING | `resumes.services.claim_validation.py` | REUSABLE |
| `CopilotContextBuilder` | EXISTING | `copilot.services.context_builder.py` | MUST MODIFY (To inject Phase 7B insights) |
| `SkillGapAnalysisService` | MISSING | N/A | MUST CREATE (Deterministic gap engine) |
| `SkillGapPriorityService` | MISSING | N/A | MUST CREATE (Priority scoring) |
| `MarketSkillDemandService` | MISSING | N/A | MUST CREATE (Market aggregate analysis) |
| `SkillDependencyService` | MISSING | N/A | MUST CREATE (Dependency graph) |
| `LearningProgressService` | MISSING | N/A | MUST CREATE (Progress tracking) |
| `SkillGapClosureService` | MISSING | N/A | MUST CREATE (Evidence-based gap closure) |
| `SkillRequirementNormalizationService`| MISSING | N/A | MUST CREATE |

## 3. Obsolete / Legacy Implementations

| Obsolete Component | Status | Location | Action Required |
| --- | --- | --- | --- |
| `SkillGapAnalysisView` | BROKEN | `ai_engine.views.SkillGapAnalysisView` | MUST DEPRECATE / OVERWRITE (Currently uses raw resume text and directly prompts the LLM, violating Phase 2+ architecture) |
| `LearningRoadmapView` | BROKEN | `ai_engine.views.LearningRoadmapView` | MUST DEPRECATE / OVERWRITE (Takes array from frontend directly to LLM, ignoring deterministic priority and verified bounds) |

## Summary
The audit confirms that the verified data pipeline (Phase 2-4) and Career Copilot (Phase 7A) foundations are intact. However, the existing `SkillGapAnalysisView` and `LearningRoadmapView` inside `ai_engine` are obsolete prototypes that violate the strict CandidateContextService trust boundary. The entire Skill Gap, Roadmap, and Recommendation domains must be designed from scratch using the deterministic rules specified in the Phase 7B prompt.
