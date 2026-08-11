# Phase 5F: Server-Side Auto-Apply Orchestration & Execution Engine

## Overview
Phase 5F implements the background worker architecture required for server-side automatic application execution. It isolates execution into a Celery-backed worker environment, utilizing Microsoft Playwright to orchestrate headless browser interactions.

## Key Features
1. **Strict Capability Flags**: Providers must explicitly have `server_execution_allowed=True` to be executed on the backend. This prevents unauthorized execution of strict platforms like LinkedIn and Indeed.
2. **Atomic Execution Locks**: To prevent concurrent executions from bypassing daily/weekly limits or submitting duplicates, `ExecutionReservationService` uses database-level locks (`select_for_update`) to strictly serialize execution slots.
3. **Isolated Browser Worker**: `ServerBrowserExecutionService` executes within a fresh `new_context()` via Playwright, ensuring cookies/sessions are never leaked across users.
4. **CAPTCHA/Auth Defense**: When a CAPTCHA or Auth prompt is detected, the execution is immediately blocked and a `UserActionRequired` flag is generated. The execution gracefully transitions to `FAILED` instead of looping indefinitely.
5. **Orchestrator**: `AutoApplyOrchestrator` runs periodically (via `AutoApplyScheduler`), discovers jobs, validates matching/policy constraints, and queues them into the Execution Domain.

## APIs
- `GET /api/automation/auto-apply/config/`
- `PATCH /api/automation/auto-apply/config/`
- `POST /api/automation/auto-apply/enable/`
- `POST /api/automation/auto-apply/pause/`
- `GET /api/automation/auto-apply/runs/`
- `GET /api/automation/auto-apply/action-required/`

## Testing
The `test_phase5f.py` test suite runs a local `MockATSServer` fixture on port `8099`, validating that Playwright succeeds on standard forms and correctly blocks when CAPTCHA is injected (`/captcha` route).
