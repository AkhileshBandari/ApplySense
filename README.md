# ApplySense AI

ApplySense AI is a production-grade, AI-powered Career Operating System designed to automate job discovery, match resumes against job descriptions, tailors resumes to specific job posts, autofill job applications with human verification overlays, track job applications, and coach job seekers via custom AI pathways.

## Architecture

- **`backend/`**: Django REST Framework backend with PostgreSQL database, Redis caching, Playwright automation workers, and an AI Fallback Manager.
- **`frontend/`**: React, TypeScript, Tailwind CSS, Chart.js web dashboard.
- **`extension/`**: Manifest V3 Chrome Extension for automatic parsing, score overlay, and smart autofill on platforms like Workday, Greenhouse, Ashby, and Lever.
- **`desktop/`**: Electron wrapper with SQLite database for offline evaluation and privacy.

## Development Setup

See the individual service directories for configuration guides:
- [Backend Development Guide](backend/README.md)
- [Frontend Development Guide](frontend/README.md)
- [Chrome Extension Guide](extension/README.md)
- [Desktop App Guide](desktop/README.md)
