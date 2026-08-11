# Phase 6: Analytics Architecture

## Overview
Phase 6 introduces a fully deterministic, database-driven analytics engine designed to provide actionable intelligence regarding a user's job search. It explicitly avoids hallucinated or AI-invented statistics by computing metrics strictly from authoritative Application, JobMatch, and Automation history records.

## Components
1. **Analytics App (`backend/analytics/`)**: A dedicated Django app responsible for all data aggregation.
2. **Service Layer**:
    - `base.py`: Handles date-range and dimension filtering.
    - `kpi_service.py`: Computes overarching KPIs.
    - `funnel_service.py`: Computes the step-by-step conversion funnel.
    - `timeline_service.py`: Uses `ApplicationStatusHistory` to compute precise timestamps and velocity.
    - `performance_service.py`: Computes conversion rates grouped by Country, Source, Provider, Match Score, or Resume Version.
    - `automation_service.py`: Tracks policy blocks, required user actions, and manual-vs-auto comparisons.
    - `insight_engine.py`: A rule-based engine that scans the deterministic data and outputs actionable insights based on configured thresholds (e.g., `MIN_COMPARISON_SAMPLE_SIZE`).

## Security & Privacy
All endpoints are strictly authenticated and authorized. Data queries inherently scope to `request.user` utilizing standard Django ORM `filter(user=request.user)` to ensure no cross-user data leakage.
