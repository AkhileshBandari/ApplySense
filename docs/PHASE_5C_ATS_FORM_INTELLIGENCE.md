# Phase 5C: ATS Form Intelligence & Safe Autofill

## Overview
Phase 5C introduces the ability to intelligently detect, extract, and safely autofill Application Tracking System (ATS) portals (Greenhouse, Lever, Ashby, etc.) via a browser extension.

## Safety & Trust Boundaries
This phase adheres to the strict rule: **ApplySense must never make a consequential application decision autonomously.**

1.  **No Automatic Submissions**: The system stops entirely before submission. The `.submit()` method is forbidden in the extension codebase.
2.  **Consent Preservation**: Fields mapping to `LEGAL_CONSENT` (e.g., terms and conditions, signatures) or `DEMOGRAPHIC_OPTIONAL` are strictly marked as `NEVER_AUTOFILL`.
3.  **Phase 5B Policy Enforcement**: Before any fields are mapped, the `FormIntelligenceService` verifies the user's `AutomationPolicyEvaluator`. If the policy triggers a `BLOCK` (e.g., due to a global pause or exceeding limits), the form resolution halts.

## Architecture

### 1. Extension (Frontend)
Located in `/extension`, built with Vite.
-   **`ApplicationPageDetector`**: Identifies the provider by URL and DOM heuristics.
-   **`BaseAdapter`**: Interface defining `extractForm()` and `fillField()`. Implementations exist for Greenhouse, Lever, Ashby, and a Generic fallback.
-   **DOM Fixture Testing**: The extension includes a Vitest suite ensuring adapters safely interact with the DOM.

### 2. Form Intelligence Service (Backend)
-   **`FormSession`**: Tracks an active autofill cycle.
-   **`DetectedApplicationForm` & `DetectedApplicationFormField`**: Stores the normalized schema.
-   **`FormIntelligenceService`**: Ties together field classification, the `ApplicationAnswerResolver` for fetching verified facts, and safety constraints.

## Flow
1. User clicks "Autofill" in extension.
2. Extension detects provider (e.g., Greenhouse).
3. Extension extracts `<input>`, `<select>`, `<textarea>` and labels.
4. Extension POSTs raw schema to `/api/applications/<id>/form-session/analyze/`.
5. Backend classifies fields to canonical keys (e.g., `FIRST_NAME`).
6. Backend resolves answers safely, evaluating policies.
7. Backend responds with `SAFE_AUTOFILL`, `REVIEW_AUTOFILL`, or `USER_INPUT_REQUIRED`.
8. Extension safely populates `SAFE_AUTOFILL` fields using DOM events (`change`/`input`) to trigger frontend framework reactivity.
9. User reviews remaining fields manually.
