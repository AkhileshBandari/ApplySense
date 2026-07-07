# ApplySense AI - Production-Grade Career Operating System Plan

ApplySense AI is an AI-powered Career Operating System designed to automate job discovery, match resumes against job descriptions, tailor CVs, autofill job applications with human approval, track progress, and provide AI-driven career coaching. It acts as an enterprise-grade platform wrapper around the intelligence foundations inspired by `career-ops`, expanding it into a full-scale web, browser extension, and desktop ecosystem.

---

## Architecture Blueprint

The ecosystem consists of five main packages/services:
1. **Backend API (`backend/`)**: Django + Django REST Framework + PostgreSQL + Redis. Hosts the AI intelligence, database models, background Playwright scrapers, and analytics.
2. **Frontend Dashboard (`frontend/`)**: React + TypeScript + TailwindCSS + Chart.js. High-fidelity web application with rich analytics, drag-and-drop resume managers, and tracking interfaces.
3. **Chrome Extension (`extension/`)**: Manifest V3 extension. Detects job portals, scrapes job details, overlays scorecards, and autofills forms.
4. **Desktop App (`desktop/`)**: Electron wrapper. Combines local database capabilities (SQLite fallback) with offline resume evaluation, matching, and privacy modes.
5. **Docker & CI/CD Config (`docker/` & `.github/`)**: Configures containers for deployment and sets up build/lint/test workflows.

### System Architecture Diagram
```mermaid
graph TD
    User([User]) <--> Extension[Chrome Extension MV3]
    User <--> Desktop[Electron Desktop App]
    User <--> WebFront[React Frontend Dashboard]
    
    Extension <-->|API / REST| Backend[Django REST Backend]
    Desktop <-->|API / Local SQLite| LocalCore[Desktop Logic]
    WebFront <-->|API / REST| Backend
    
    Backend <-->|SQL Queries| DB[(PostgreSQL)]
    Backend <-->|Caching & Queue| Cache[(Redis / Celery)]
    Backend <-->|AI Tasks| AILayer[AI Fallback Manager]
    Backend <-->|Local Automation| Automation[Playwright Worker]
    
    AILayer --
<truncated 11696 bytes>
