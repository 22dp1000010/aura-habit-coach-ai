# Aura: AI Habit Coach & Behavior Assistant

Aura is a Generative AI-powered web application designed to help users identify, track, and reduce or overcome harmful habits or addictions (such as excessive screen time, doomscrolling, late-night snacking, or smoking). 

By combining daily tracking logs with Cognitive Behavioral Therapy (CBT) and Acceptance and Commitment Therapy (ACT) principles delivered through a Groq-powered AI coach, Aura empowers sustained behavior change.

🚀 **Deployed Application:** [https://aura-habit-coach-ai.vercel.app/](https://aura-habit-coach-ai.vercel.app/).

---

## 🛠️ Technology Stack

*   **Frontend:** React (scaffolded via Vite), standard CSS variables, and Lucide React icons.
*   **Backend:** Python FastAPI for asynchronous API endpoints.
*   **Database:** SQLite via SQLAlchemy ORM (file-based locally, support for Postgres/Turso remotely).
*   **GenAI Engine:** Groq Cloud API using `llama-3.1-8b-instant` for low-latency empathetic coaching.
*   **Testing:** Pytest and Pytest-Asyncio with automated API mocking.

---

## ✨ Features

1.  **Personalized Habit Onboarding:** Configure target habit names, triggers, internal motivations, and baseline metrics.
2.  **Aura's Daily Nudge:** The dashboard displays a dynamic, context-aware nudge derived from your recent tracking streaks or slip-ups.
3.  **Daily Check-in Logs:** Record numeric logs, craving levels (1-10 slider), slip-up tags, and trigger reflections.
4.  **CBT Coaching Chat:** Chat with Aura about triggers or behavior routines.
5.  **SOS Urge Surfing Button:** Click to instantly load an emergency grounding somatic routine (box breathing, 5-4-3-2-1 grounding) to surf urges safely.
6.  **Progress History:** A tabular historical index listing all logs.
7.  **Reset Panel:** A developer configuration to reset simulated databases and start fresh.

---

## ⚙️ Running Locally

### Prerequisite: Setup API Key
Obtain a Groq API key from the [Groq Console](https://console.groq.com/) and export it to your environment:
```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_..."

# macOS/Linux Bash
export GROQ_API_KEY="gsk_..."
```

### 1. Start the FastAPI Backend
From the root directory, install Python requirements and start Uvicorn:
```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The server will start at [http://127.0.0.1:8000](http://127.0.0.1:8000). You can inspect health status at `/api/health`.

### 2. Start the Vite React Frontend
Navigate to the `frontend` directory, install packages, and start the development server:
```bash
cd frontend
npm install
npm run dev -- --port 5173
```
Open [http://localhost:5173/](http://localhost:5173/) in your web browser.

---

## 🧪 Running Tests

Aura includes a unit test suite to test schemas, inputs validation, habit tracking logic, and mock Groq completions.
Run pytest from the root folder:
```bash
python -m pytest backend/tests/
```

---

## ☁️ Deploying to Vercel

Aura is pre-configured to build and run on Vercel as a monorepo via `vercel.json` and serverless routes:

1.  **Push the repository to GitHub**:
    Ensure your local `.gitignore` is active so local caches and `aura.db` are excluded.
2.  **Create a Vercel project**:
    Link your GitHub repository to Vercel. Vercel will discover `vercel.json` and build the React app and Python APIs.
3.  **Set Environment Variables in Vercel**:
    *   `GROQ_API_KEY`: Your Groq API credentials. This is the only variable required! All habits, tracking histories, and coach chat logs are stored securely in the user's local browser `localStorage`.
