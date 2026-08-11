# Analytics Metric Definitions

This document ensures semantic stability across all KPI and funnel calculations in Phase 6.

## `total_jobs_matched`
- **Definition:** The number of jobs that were discovered, analyzed, and generated a match score for the user.
- **Source Table:** `JobMatch`
- **Timestamp Source:** `created_at` (mapped via date filter)

## `applications_created`
- **Definition:** Total application records created in the database.
- **Numerator:** Count of `Application.id`
- **Source Table:** `Application`
- **Timestamp Source:** `created_at`

## `applications_submitted`
- **Definition:** Applications that successfully completed submission to an employer.
- **Numerator:** Count of `Application.id` where status is in `SUBMITTED_STATES`
- **Included States:** `SUBMITTED`, `UNDER_REVIEW`, `ASSESSMENT`, `INTERVIEW`, `FINAL_ROUND`, `OFFER`, `REJECTED`, `ACCEPTED`, `DECLINED`
- **Excluded States:** `DRAFT`, `PREPARING`, `REVIEW_REQUIRED`, `READY_TO_SUBMIT`, `SUBMITTING`, `APPLICATION_FAILED`, `WITHDRAWN`, `UNKNOWN`
- **Timestamp Source:** `created_at`

## `responses`
- **Definition:** Submitted applications that received a meaningful progression response from the employer.
- **Numerator:** Count of `Application.id` where status is in `RESPONSE_STATES`
- **Included States:** `ASSESSMENT`, `INTERVIEW`, `FINAL_ROUND`, `OFFER`, `REJECTED`, `ACCEPTED`, `DECLINED`
- **Timestamp Source:** `created_at` (for base bucketing)

## `interviews`
- **Definition:** Applications that reached at least the interview stage.
- **Numerator:** Count of `Application.id` where status is in `INTERVIEW_STATES`
- **Included States:** `INTERVIEW`, `FINAL_ROUND`, `OFFER`, `ACCEPTED`, `DECLINED`
- **Timestamp Source:** `created_at`

## `offers`
- **Definition:** Applications that resulted in an offer.
- **Numerator:** Count of `Application.id` where status is in `OFFER_STATES`
- **Included States:** `OFFER`, `ACCEPTED`, `DECLINED`

## `rejections`
- **Definition:** Applications that were explicitly rejected.
- **Numerator:** Count of `Application.id` where status is `REJECTED`

## Rates (Conversion)
- **response_rate:** `(responses / applications_submitted) * 100`
- **interview_rate:** `(interviews / applications_submitted) * 100`
- **offer_rate:** `(offers / applications_submitted) * 100`
- **rejection_rate:** `(rejections / applications_submitted) * 100`

## Timeline Metrics
- **Time to Response / Interview / Offer:**
- Calculated by querying `ApplicationStatusHistory` to find the exact delta in days between the `submitted_at` timestamp and the first occurrence of the target status. Calculated dynamically with both Average and Median to avoid skew by outlier application histories.
