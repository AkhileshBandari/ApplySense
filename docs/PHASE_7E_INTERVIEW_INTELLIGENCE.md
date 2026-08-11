# Phase 7E: Interview Intelligence Architecture

## Overview
Phase 7E introduces a comprehensive Interview Intelligence module to ApplySense. It focuses on personalized mock interviews, deterministic scoring, and closed-loop feedback mechanisms that integrate with a candidate's existing context (Resume, Skill Gaps).

## Core Concepts
1. **Interview Plan**: A tailored curriculum mapping to a specific role/difficulty.
2. **Mock Session**: An active interview loop tracking duration, state, and readiness.
3. **Question Generation**: Grounded in `JobRequirements` or `Resume` claims.
4. **Evaluators**: Split between deterministic rule checks (STAR structure) and semantic feedback (Technical accuracy).
5. **Adaptive Follow-Ups**: LLM limits recursion to `MAX_FOLLOW_UP_DEPTH` to prevent endless loops.
6. **Improvement Loop**: Feedback feeds back into the Phase 7B `LearningRoadmap` for continuous improvement.

## Boundaries Preserved
- **Candidate Context Immunity**: Mock interview responses never overwrite a candidate's verified context. Any new skill mentioned in an interview remains an unverified claim.
- **Fail-Closed Evaluation**: If the AI evaluator fails, a deterministic fallback ensures the system degrades gracefully rather than crashing.
- **Prompt Injection Defense**: Evaluators isolate the candidate response within delimited brackets (`[START ANSWER] ... [END ANSWER]`) and are instructed to ignore out-of-bounds instructions.

## Data Models (`interviews/models.py`)
- `InterviewPlan`, `InterviewPlanSection`
- `MockInterviewSession`
- `InterviewQuestion`, `InterviewResponse`, `InterviewResponseEvaluation`
- `InterviewWeakness`, `InterviewImprovementPlan`
