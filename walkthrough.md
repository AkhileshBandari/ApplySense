# ApplySense AI - Walkthrough of Implementation

We have successfully engineered and populated the full codebase for **ApplySense AI** inside the workspace directory. Below is a detailed walkthrough of all components and where you can access them.

---

## 1. Backend Service (`backend/`)
The backend is built using **Django** and **Django REST Framework** with modular apps to support scaling.

* **Settings & Setup**:
  - [settings.py](file:///e:/projects/ApplySense-AI/backend/applysense/settings.py): Central configuration mapping JWT simplejwt parameters and PostgreSQL setup with SQLite fallback for offline usage.
  - [requirements.txt](file:///e:/projects/ApplySense-AI/backend/requirements.txt): Python dependencies including Playwright, PyPDF, and AI SDKs.
* **Authentication**:
  - [models.py](file:///e:/projects/ApplySense-AI/backend/authentication/models.py): Custom User model supporting `candidate` and `admin` roles.
  - [tests.py](file:///e:/projects/ApplySense-AI/backend/authentication/tests.py): Asserts registration, login validation, and profile auto-creation.
* **Profile System**:
  - [models.py](file:///e:/projects/ApplySense-AI/backend/profiles/models.py): DB representations of experiences, certifications, skills, and academic history.
* **AI Orchestrator & Fallback**:
  - [fallback_manager.py](file:///e:/projects/ApplySense-AI/backend/ai_engine/fallback_manager.py): The core AI Fallback Manager. Tries OpenAI -> Groq -> OpenRouter -> HuggingFace, with a rule-based mock backup system if offline.
* **Resume Parsing & Health Intelligence**:
  - [parser.py](file:///e:/projects/ApplySense-AI/backend/resumes/parser.py): Custom text extraction from PDF/DOCX files and health checker rules.
  - [views.py](file:///C:/Users/
<truncated 3609 bytes>
