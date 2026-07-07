# ApplySense AI Setup Guide

Follow these instructions to run the ApplySense AI system locally or in production containers.

---

## 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Docker & Docker Compose** (Optional, for containerized deployments)

---

## 2. API Configurations
1. Copy `.env.example` at the project root to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configure your API keys. We highly recommend configuring at least one AI provider (e.g. `OPENAI_API_KEY` or `GROQ_API_KEY`) to run semantic evaluations.

---

## 3. Running with Docker Compose (Recommended)
Boot all services (PostgreSQL, Redis, Django, and React) in a single command:
```bash
docker-compose up --build
```
- Web Dashboard: `http://localhost:3000`
- REST Backend API: `http://localhost:8000`

---

## 4. Manual Local Setup

### Backend API
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations and start server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

### Frontend Dashboard
1. Navigate to the frontend folder:
   ```bash
   cd ../frontend
   ```
2. Install npm modules:
   ```bash
   npm install
   ```
3. Boot the Vite dev server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your web browser.

---

## 5. Installing the Chrome Extension
1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (toggle at top right).
3. Click **Load unpacked** (top left).
4. Select the `extension/` folder inside this repository.
5. The ApplySense floating scorecard will now render automatically when you open Greenhouse, Lever, Ashby, or LinkedIn job detail pages!

---

## 6. Running the Electron App
1. Navigate to the desktop folder:
   ```bash
   cd ../desktop
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Electron shell:
   ```bash
   npm start
   ```
   *Note: Ensure the React frontend dev server (`http://localhost:3000`) is running, as Electron bridges and frames it directly.*
