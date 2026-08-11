# ApplySense Phase 7H: Unified Career Execution & Progress Orchestration

## Overview
Phase 7H transforms the Career Decision Action Planner (Phase 7G) into a trackable, deterministic execution engine. The engine reconciles dynamic plan versions into a persistent log of completed, active, and blocked career execution items while enforcing strict safety boundaries before automated tasks can run.

## Core Architecture

### App: `career_execution`

#### Models
1. **CareerExecutionPlan**: The central container for a candidate's continuous progress.
2. **CareerExecutionItem**: The normalized action. Persistent across Phase 7G plan changes. State transitions are governed by Execution Modes (`USER_ACTION`, `ASSISTED`, `REVIEW_REQUIRED`, `AUTO_EXECUTABLE`, `SYSTEM_OBSERVATION`, `BLOCKED`).
3. **CareerExecutionDependency**: Permanent dependency graph between `CareerExecutionItem`s.
4. **CareerExecutionProgress**: Generates a strictly bounded (0-100) snapshot of execution scoring across multiple domains (Skills, Brand, Interviews, Applications).
5. **CareerExecutionOutcome**: Captures success/failure details upon completion.
6. **CareerExecutionEvent**: Append-only log to trace candidate execution trajectory.

### Key Services

1. **`ActionReconciliationService`**: 
   Transforms `CareerDecisionPlanVersion` outputs into `CareerExecutionItem`s without duplication. Updates dynamic parameters (impact score, urgency) while keeping execution state intact. Missing incomplete actions are marked `SUPERSEDED`.
2. **`ExecutionEligibilityService`**:
   The safety boundary. It strictly blocks execution of any item if prerequisites are unmet. Before granting `AUTO_EXECUTABLE` mode (e.g., auto-applying), it defers to `AutoApplyEligibilityService` to enforce constraints (e.g., API keys present, limit not reached, opt-in true).
3. **`CareerProgressEngine`**:
   Generates a deterministic (non-LLM) mathematical progress calculation to track candidate velocity.
4. **`ExecutionLifecycleService`**:
   Manages state transitions. Marking an item `COMPLETED` unblocks dependent items and initiates immediate recalculation of eligibility.

## Safety & Trust

1. **Context Boundary**: 
   The Copilot integration injects execution data explicitly marked as `CAREER_EXECUTION_DATA_IS_ADVISORY`. Copilot cannot complete actions or override blocking policies.
2. **Deterministic State Check**: 
   `AUTO_EXECUTABLE` bypasses are hard-blocked by Phase 5 policy hooks.
3. **Immutability**:
   `CareerExecutionEvent` and `CareerExecutionOutcome` are append-only.

## APIs & Integration
- `GET /api/career-execution/current/`: Yields active reconciled plan.
- `GET /api/career-execution/progress/`: Yields current progress bounded score.
- `GET /api/career-execution/next_action/`: Yields highest-impact unblocked action.
- `POST /api/career-execution/items/{id}/complete/`: Transitions state and recalculates downstream dependency eligibility.

*This concludes the architectural implementation of Phase 7H.*
