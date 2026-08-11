# Phase 5E: Global Platform Expansion, ATS Adapters & Capability Certification

## Overview
Phase 5E expands ApplySense from an initial pilot targeting Greenhouse, Lever, and Ashby into a robust, granular platform capable of interacting with Enterprise ATS networks (Workday, SmartRecruiters, Workable, etc.) while preventing catastrophic automation failures.

## Key Architectural Upgrades

### 1. Decoupling Job Source from Application Provider
Historically, a job could just have a "source". Now, the pipeline distinguishes between:
- **Job Source**: Where the job was found (e.g. LinkedIn, Indeed, Adzuna). Governed by `SourceCapability`.
- **Application Provider**: The underlying ATS system hosting the application (e.g. Workday, Lever). Governed by `PlatformCapability`.

**JobSourceOccurrence Model**
This allows the same canonical job (e.g. "Software Engineer at Acme") to be tracked across multiple job boards. The `Job.canonical_hash` handles deduplication, ensuring that if a user clicks an Indeed link and a LinkedIn link for the same job, it maps to a single `Application` execution path.

### 2. Form Intelligence & Provider Re-Detection
Because job boards often perform opaque redirects, `PreExecutionValidationService` has been upgraded to include a **Re-Detection Mechanism**. 
Just before locking execution, the router compares the `FormSession.provider` detected live by the extension against the expected `Job.application_provider`. If there is a mismatch (e.g., a LinkedIn Easy Apply job actually redirects to a Workday portal), execution is aborted for safety.

### 3. Capability Certification Matrix
Platforms are now rigorously defined in `jobs.registries.py`:

```python
class PlatformCapability:
    provider_detection: bool 
    form_detection: bool 
    field_extraction: bool 
    field_classification: bool 
    safe_autofill: bool 
    user_confirmed_browser_submit: bool 
    authorized_api_submit: bool 
    
    captcha_possible: bool
    authentication_possible: bool
    
    implementation_status: ImplementationStatus 
    certification_status: CertificationStatus 
```

**Certification Posture**:
- **Workday, SmartRecruiters, Workable** are now implemented for DOM intelligence but are strictly prevented from auto-submitting.
- **Generic ATS** is allowed to autofill but defaults to `user_confirmed_browser_submit = False`.

### 4. Extension Adapters
- `BaseAdapter` now enforces an `AdapterCapabilities` contract.
- Added robust selectors for `WorkdayAdapter.ts` targeting `data-automation-id`.
- Added robust selectors for `SmartRecruitersAdapter.ts` targeting `.form-group`.
- Added robust selectors for `WorkableAdapter.ts` targeting `data-ui`.

All extension components achieved 100% test pass rates across detecting capabilities and DOM extraction.
