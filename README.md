# AI Resume Screening & Ranking System

A production-minded, CLI-first Python system that ingests a directory of candidate resumes in PDF format, applies deterministic hard eligibility filters, scores eligible candidates across engineering and AI depth dimensions, enriches profiles with public GitHub activity, and produces an explainable, ranked shortlist in machine-readable JSON.

---

## 1. Project Overview & Architecture

The system processes resumes in a sequential, fault-isolated pipeline where failures on any individual resume (corrupt PDF, LLM timeout, GitHub rate limit) never crash the batch.

```
Input Directory (*.pdf)
       │
       ▼
1. PDF Parsing (parsers.py - pypdf)
   - Resilient text extraction
   - Isolated exception boundaries
       │
       ▼
2. Entity & Skills Extraction (extractor.py)
   - Deterministic regex for contact info & GitHub handles
   - Curated skill taxonomy matching
       │
       ▼
3. Deterministic Eligibility Check (eligibility.py)
   - Python evidence check (skills, projects, or experience)
   - Meaningful AI/agentic project check
   - Non-rejection of mixed-stack profiles (Java/React + Python + AI)
   - Disqualified profiles routed to rejected list with explicit reasons
       │
       ▼
4. Semantic Project Analysis (llm_client.py)
   - Structured Pydantic extraction (depth, tools, wrappers, tutorials)
   - Pluggable adapter (Gemini API with google-genai)
   - Deterministic heuristic fallback for offline or key-less execution
       │
       ▼
5. Lightweight GitHub Enrichment (github_client.py)
   - Public GitHub REST API query with in-run memory cache
   - Activity score (0–5) + maintained Python/AI repo score (0–5)
   - Positive signal only; rate limits (403) or missing profiles score 0 without penalty
       │
       ▼
6. Deterministic 100-Point Scoring (scorer.py)
   - AI / Agentic Depth: 0–40 pts
   - Python & Backend: 0–30 pts
   - Cloud & Full Stack: 0–15 pts
   - GitHub Activity: 0–10 pts
   - Engineering Depth Signals: 0–5 pts
   - Quality Penalties: -5 to -15 pts (thin wrapper), -5 pts (tutorial clone)
   - Clamped within [0, 100] with deterministic tie-breaking
       │
       ▼
7. Output & Reporting (reporter.py)
   - Writes complete structured output to results.json
   - Prints clean, explainable terminal summary table
```

---

## 2. Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- `uv` (recommended) or standard `pip` / `venv`

### Option A: Using `uv` (Fastest)
```bash
git clone <repo-url>
cd AI-resume

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Option B: Using Standard Python `venv`
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Environment Variables Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

| Variable | Required? | Default | Description |
| :--- | :---: | :---: | :--- |
| `GEMINI_API_KEY` | Optional | `""` | Google Gemini API key for structured semantic project analysis. If omitted, the system seamlessly uses the built-in deterministic heuristic analyzer. |
| `GEMINI_MODEL` | Optional | `gemini-2.5-flash` | Gemini model name for analysis. |
| `GITHUB_TOKEN` | Optional | `""` | GitHub Personal Access Token to avoid public unauthenticated rate limits (60 requests/hour). If omitted, public endpoints are queried. |

---

## 4. Running the System

### Basic CLI Usage
```bash
# Activate virtual environment
source .venv/bin/activate

# Run screening against the resume directory
python main.py --input ./resumes --output ./output/results.json
```

### Generating Test Fixtures
If the input directory is empty, generate the 8 focused test fixture resumes:
```bash
python generate_sample_resumes.py
python main.py --input ./resumes --output ./output/results.json
```

### CLI Options
- `--input`, `-i`: Directory containing candidate PDF resumes (default: `./resumes`).
- `--output`, `-o`: Filepath where the JSON results should be saved (default: `./output/results.json`).
- `--verbose`, `-v`: Enable detailed debug/info logs.

---

## 5. Output Format

The output is written to `results.json` matching the assignment specification:

```json
{
  "batch_summary": {
    "total_resumes": 8,
    "successfully_parsed": 7,
    "eligible": 5,
    "rejected": 3,
    "failed_or_unreadable": 1,
    "duplicates": 0
  },
  "ranked_candidates": [
    {
      "rank": 1,
      "candidate_name": "Asha Rao",
      "file_name": "candidate_01_asha_rao.pdf",
      "eligible": true,
      "rejection_reasons": [],
      "total_score": 89,
      "score_breakdown": {
        "ai_project_depth": 40,
        "python_backend": 30,
        "cloud_fullstack": 12,
        "github": 2,
        "engineering_depth": 5,
        "penalties_applied": 0,
        "evidence_map": {
          "ai_project_depth": "Identified stateful or agentic orchestration in candidate profile (e.g. LangGraph / Multi-Agent / Tool Calling).",
          "python_backend": "Backend engineering stack: Python core + Async FastAPI backend + PostgreSQL & Redis datastores (30/30).",
          "cloud_fullstack": "Docker containerization, Cloud infrastructure (GCP), CI/CD or orchestration (12/15).",
          "github": "Active profile (1/5 activity); 0 relevant/maintained Python/AI repo(s) (1/5 repos).",
          "engineering_depth": "Automated testing with Pytest; Caching strategies; Asynchronous task queues; Concurrency & observability (5/5)."
        }
      },
      "matched_skills": [
        "Python", "FastAPI", "PostgreSQL", "Redis", "SQLAlchemy", "AsyncIO", "Celery",
        "LangChain", "LangGraph", "Vector Search", "Tool Calling", "Multi-Agent",
        "ChromaDB", "Docker", "GCP", "CI/CD", "Pytest", "Caching"
      ],
      "project_summary": "Architected a multi-agent / stateful agentic system with tool calling and orchestration.",
      "github_summary": "Active profile (1/5 activity); 0 relevant/maintained Python/AI repo(s) (1/5 repos).",
      "strengths": [
        "Demonstrates practical multi-agent / agentic workflow architecture",
        "Strong async backend engineering with FastAPI and relational/caching datastores",
        "Hands-on containerization and cloud deployment exposure"
      ],
      "concerns": []
    }
  ],
  "rejected_candidates": [
    {
      "candidate_name": "Dev Patel",
      "file_name": "candidate_03_dev_patel.pdf",
      "eligible": false,
      "rejection_reasons": ["No AI/agentic project evidence"],
      "matched_skills": ["Python", "Django", "PostgreSQL", "Redis", "Celery", "Docker"]
    },
    {
      "candidate_name": "Priya Nair",
      "file_name": "candidate_04_priya_nair.pdf",
      "eligible": false,
      "rejection_reasons": ["No evidence of Python stack"],
      "matched_skills": ["LangChain", "React", "Next.js", "TypeScript", "Node.js", "Java", "Spring Boot"]
    },
    {
      "candidate_name": "Unknown Candidate",
      "file_name": "candidate_08_corrupt.pdf",
      "eligible": false,
      "rejection_reasons": ["Unreadable file: PDF parsing error: PdfReadError: startxref not found"],
      "matched_skills": []
    }
  ]
}
```

---

## 6. Running Tests

Run the test suite with `pytest`:
```bash
source .venv/bin/activate
pytest -v
```

All 19 focused tests cover:
- Python + AI eligible candidates
- Python-only rejection
- AI-only rejection
- Mixed-stack (Java/React + Python + AI) acceptance
- Thin-wrapper penalty deduction (-10 pts)
- Tutorial clone penalty deduction (-5 pts)
- Score clamping [0, 100]
- Parser resilience on corrupt and empty PDF files
- Graceful handling of GitHub 404, 403 (rate limits), and network timeouts

---

## 7. Design Decisions

### 1. Deterministic Eligibility vs. Semantic Analysis
Hard eligibility filtering is intentionally kept **100% deterministic and outside the LLM**.
- Real-world hiring systems cannot afford stochastic rejections of qualified candidates.
- Python evidence is confirmed from skills, project descriptions, or ecosystem frameworks (`FastAPI`, `Flask`, `Django`, `AsyncIO`).
- AI evidence is confirmed from recognized frameworks (`LangGraph`, `LangChain`, `LlamaIndex`, `CrewAI`) and architecture patterns (`RAG`, `Vector Search`, `Tool Calling`).
- **Non-rejection rule**: Candidates with mixed backgrounds (e.g. Java, React, Next.js) are **never** rejected if they meet the Python + AI requirement.

### 2. Scoring & Penalty Strategy
Scoring strictly adheres to the assignment's 100-point rubric:
- **AI / Agentic / RAG Project Depth (40 pts)**: Rewards real system architecture. Autonomous agents and multi-agent systems receive top marks (35–40); practical RAG with vector DBs receives 25–30; basic API prompts receive 15.
- **Python & Backend Engineering (30 pts)**: Rewards FastAPI, async programming, PostgreSQL, and Redis in projects over keyword lists.
- **Cloud / Deployment / Full Stack (15 pts)**: Rewards Docker, cloud deployment (GCP/AWS), and modern frontend integration.
- **GitHub Activity (10 pts)**: Scored on recent commit/update frequency (0–5) and maintained Python/AI repositories (0–5).
- **Engineering Depth Signals (5 pts)**: Rewards automated testing (`pytest`), caching, async queues, and observability.
- **Project-Quality Penalties**:
  - Thin API wrappers (projects that merely wrap OpenAI completion calls without retrieval, state, or custom backend logic) are penalized **-10 points**.
  - Generic uncustomized tutorial clones are penalized **-5 points**.
  - Scores are clamped within `[0, 100]`.

### 3. Dual-Mode LLM Adapter & Graceful Fallback
- When `GEMINI_API_KEY` is present, the system leverages Gemini with structured Pydantic schema validation (`LLMAnalysisResult`) to evaluate project depth and identify wrappers.
- When no API key is provided, or if network calls fail, the system activates a **deterministic heuristic analyzer**. This guarantees 100% testability, zero external spending, and zero crashes.

### 4. Lightweight GitHub Enrichment
- Uses only 2 lightweight public REST queries (`/users/{username}` and `/users/{username}/repos`).
- Employs an in-run memory cache to eliminate redundant network roundtrips.
- Timeouts are bounded to 3.0s.
- GitHub is **strictly a positive signal**. A missing profile, private account, 404 error, or 403 rate limit never affects eligibility or stops screening.

---

## 8. If I Had More Time

1. **OCR / Scanned PDF Support**: Add a fallback OCR pipeline (e.g. `pytesseract` or Gemini Vision) for scanned, image-only resumes.
2. **Bounded Concurrency (`asyncio` / ThreadPool)**: Process candidate files and GitHub enrichments concurrently with `asyncio.Semaphore(5)` to accelerate processing on batches of 500+ resumes.
3. **Interactive Terminal Dashboard**: Integrate `rich` to render colored summary tables and candidate score breakdowns directly in the terminal.
4. **FastAPI Endpoints**: Wrap `pipeline.py` in lightweight `POST /screen` and `GET /results` endpoints for programmatic service integration.
