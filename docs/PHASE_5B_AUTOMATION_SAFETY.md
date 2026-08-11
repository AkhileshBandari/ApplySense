# PHASE 5B — AUTOMATION SAFETY & USER RULES

## Mission
Ensure absolute user control over application automation, implementing strict safety boundaries and user-configurable rules that govern the automatic submission process.

## Key Architectures

### 1. The Automation Policy Evaluator
We created an `AutomationPolicyEvaluator` which acts as the supreme court for automation decisions. It reviews an application before submission, checking against global safety protocols and user-specific rules. It yields a `PolicyDecision` (PROCEED, REQUIRE_REVIEW, or BLOCK) with corresponding reason codes (e.g. `MATCH_SCORE_TOO_LOW`, `EXCLUDED_COMPANY_MATCHED`).

### 2. Automation Policies & Rules
- `AutomationPolicy`: A model that stores a user's overarching settings, such as `automation_enabled` (default `False`), `daily_application_limit`, and `minimum_match_score`. It also includes a `global_pause` for emergencies.
- `AutomationRule`: Sub-rules attached to a policy to handle specific exclusions or inclusions (e.g. `EXCLUDED_COMPANY`).

### 3. Application Deduplication
We implemented `ApplicationDuplicateService` to detect duplicate applications for the same job and user. It ignores `DRAFT` applications, but correctly identifies previously active or submitted applications to prevent spam.

### 4. Cross-User Isolation
Rules and policies strictly belong to their users. Exclusions configured by User A have zero impact on the `AutomationPolicyEvaluator` when evaluating User B.

### 5. API & UI Integration
The evaluator logic is integrated into `ApplicationViewSet.prepare()`. When an application is prepared, the evaluator runs and the resulting `PolicyDecision` is saved and returned via the API. The frontend `ApplicationsPage` displays this information and alerts the user if an application is blocked or requires manual review due to missing information or policy violations.

## Completion Status
Phase 5B is COMPLETE and successfully tested against all requirements.
