# Take-Home Project Grader

A hiring tool for evaluating candidate take-home assignments automatically.
Upload a problem statement, paste a GitHub repo link, and get a full
evaluation report before any human reviews the code.

---

## What It Does

When a candidate submits their take-home project, this tool:

1. Reads the problem statement (PDF or Word) and extracts required features using AI
2. Fetches repository metadata via the GitHub API
3. Clones the repo and runs the actual code - build, tests, and lint
4. Scans source code to check if required features are actually implemented
5. Calculates a score across problem solving and code quality
6. Generates a written evaluation with a hire recommendation

No gut feelings. Just evidence from the actual code.

---

## Tech Stack

**Backend**
- Python 3.10+
- FastAPI
- SQLAlchemy + SQLite
- PyGithub
- pypdf + python-docx
- Groq API (LLM inference)

**Frontend**
- React + Vite
- Tailwind CSS

---

## Project Structure

```
/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy setup
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic schemas
│   ├── requirements.txt        # Python dependencies
│   ├── grader/
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Orchestrates all grading steps
│   │   ├── problem_parser.py   # PDF/Word parsing + AI extraction
│   │   ├── github_checker.py   # GitHub API checks
│   │   ├── repo_runner.py      # Clone + build/test/lint
│   │   ├── code_scanner.py     # Source code feature scanning
│   │   ├── scorer.py           # Score calculation
│   │   ├── ai_evaluator.py     # Final AI written evaluation
│   │   └── groq_client.py      # Groq API client
│   └── routers/
│       ├── __init__.py
│       └── submissions.py      # API route handlers
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── components/
│       │   ├── UploadForm.jsx
│       │   ├── RequirementsPreview.jsx
│       │   ├── ProgressTracker.jsx
│       │   ├── ReportCard.jsx
│       │   ├── TechStackPanel.jsx
│       │   ├── FeaturesPanel.jsx
│       │   ├── RepoFlags.jsx
│       │   ├── ScoreBreakdown.jsx
│       │   ├── AIEvaluation.jsx
│       │   ├── LogViewer.jsx
│       │   ├── SubmissionsTable.jsx
│       │   └── api.js          # API calls to backend
│       └── pages/
│           ├── Home.jsx
│           └── Report.jsx
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Prerequisites

Before running this project make sure you have:

- Python 3.10 or higher
- Node.js 18 or higher
- Git

And the following API keys:

- **Groq API key** - get it free at [console.groq.com](https://console.groq.com)
- **GitHub personal access token** - generate at [github.com/settings/tokens](https://github.com/settings/tokens) with `public_repo` read scope

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/NaveenKunam/takehome-project-grader.git
cd takehome-project-grader
```

### 2. Configure environment variables

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Open `.env` and set:

```
GITHUB_TOKEN=your_github_personal_access_token
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=sqlite:///./grader.db
```

### 3. Set up the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`

Auto-generated API docs available at `http://localhost:8000/docs`

### 4. Set up the frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## How to Use

1. Open `http://localhost:5173` in your browser
2. Upload a problem statement file (PDF or .docx)
3. Review the extracted requirements - confirm they look correct
4. Paste the candidate's GitHub repo URL
5. Click **Grade This Submission**
6. Watch the live progress tracker as the grader runs
7. View the full report card when complete
8. All past submissions are saved in the table below for comparison

---

## Scoring

Submissions are scored out of 100 across two categories:

**Problem Solving - 50 points**
Points divided equally across required features from the problem statement.
Each feature is assessed as implemented, partial, missing, or unclear
based on actual source code scanning.

**Code Quality - 50 points**

| Check | Points |
|---|---|
| Build succeeds | 15 |
| Tests exist | 10 |
| Tests pass | 15 |
| Lint acceptable | 10 |

**Hire Recommendation**

| Score | Recommendation |
|---|---|
| 80 - 100 | Strong Yes |
| 60 - 79 | Yes |
| 40 - 59 | Maybe |
| Below 40 | No |

---

## Supported Project Types

The grader automatically detects the candidate's tech stack and runs
the appropriate checks:

| Detected File | Project Type | Checks Run |
|---|---|---|
| package.json | Node / React / Vue | npm install, npm test, npm run build, eslint |
| requirements.txt | Python | pip install, pytest, pylint, flake8 |
| pyproject.toml | Python | pip install, pytest, pylint, flake8 |
| pom.xml | Java | Manual review recommended |
| go.mod | Go | Manual review recommended |
| Gemfile | Ruby | Manual review recommended |
| None found | Unknown | Manual review required |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/grade` | Submit a repo for grading (multipart: file + github_url) |
| GET | `/api/submissions` | List all past submissions |
| GET | `/api/submissions/{id}` | Get full report for one submission |
| GET | `/api/submissions/{id}/status` | Get current grading status (for polling) |
| DELETE | `/api/submissions/{id}` | Delete a submission |

---

## Repo Flags

The grader surfaces two flags when relevant:

- **Is a fork** - the repo was forked from another, candidate may have copied an existing solution
- **Multiple contributors** - more than one person contributed code

These are only shown when true. No flag means no concern.

---

## Limitations

- Only public GitHub repositories are supported
- Build and test commands time out after 60 seconds
- Source code scanning reads up to 50 files, 200 lines each
- Java, Go, and Ruby projects are detected but not auto-run - manual review recommended

---

## Planned Improvements

- [ ] Support for private repos
- [ ] Side-by-side candidate comparison view
- [ ] Export report as PDF
- [ ] Support for Java and Go auto-running
- [ ] Deployment guide


