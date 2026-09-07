from models import ExtractedCandidate, LLMAnalysisResult, ProjectAnalysis, GitHubResult
from scorer import compute_candidate_score, calculate_penalties

def test_score_bounds_clamped_0_to_100():
    candidate = ExtractedCandidate(
        file_name="super_dev.pdf",
        name="Super Dev",
        matched_skills=[
            "Python", "FastAPI", "AsyncIO", "PostgreSQL", "Redis", "SQLAlchemy", "Celery",
            "LangGraph", "Multi-Agent", "Tool Calling", "ChromaDB",
            "Docker", "GCP", "Kubernetes", "CI/CD", "React", "Next.js",
            "Pytest", "Caching", "Message Queues", "Observability"
        ],
        raw_text="""
        SKILLS: Python, FastAPI, AsyncIO, PostgreSQL, Redis, LangGraph, Tool Calling, Docker, GCP, Pytest
        PROJECTS:
        Super Agent Architecture
        - Architected autonomous multi-agent system using LangGraph and tool calling.
        - Built async FastAPI backend with PostgreSQL and Redis distributed caching in Python.
        - Deployed with Docker on GCP with Pytest test suites and CI/CD observability.
        """
    )
    llm_result = LLMAnalysisResult(
        projects=[
            ProjectAnalysis(
                title="Super Agent",
                ai_depth_level="autonomous_agent",
                is_thin_wrapper=False,
                is_tutorial_clone=False,
                evidence="Full multi-agent autonomous system."
            )
        ]
    )
    github_result = GitHubResult(
        activity_score=5,
        repo_score=5,
        total_score=10,
        status="success",
        summary="Top active GitHub contributor"
    )

    total_score, breakdown = compute_candidate_score(candidate, llm_result, github_result)
    assert 0 <= total_score <= 100
    assert total_score == 100
    assert breakdown.ai_project_depth <= 40
    assert breakdown.python_backend <= 30
    assert breakdown.cloud_fullstack <= 15
    assert breakdown.github <= 10
    assert breakdown.engineering_depth <= 5

def test_thin_wrapper_penalty_deduction():
    candidate = ExtractedCandidate(
        file_name="wrapper_dev.pdf",
        name="Wrapper Dev",
        matched_skills=["Python", "Flask", "OpenAI API"],
        raw_text="Built a simple wrapper around OpenAI API to answer questions."
    )
    llm_result = LLMAnalysisResult(
        projects=[
            ProjectAnalysis(
                title="GPT-4 Wrapper",
                ai_depth_level="basic_api",
                is_thin_wrapper=True,
                is_tutorial_clone=False,
                evidence="Superficial API call without retrieval or state."
            )
        ]
    )
    github_result = GitHubResult()

    penalties, reasons = calculate_penalties(llm_result)
    assert penalties >= 10
    assert any("Thin LLM/API wrapper penalty" in r for r in reasons)

    total_score, breakdown = compute_candidate_score(candidate, llm_result, github_result)
    assert breakdown.penalties_applied >= 10

def test_tutorial_penalty_deduction():
    llm_result = LLMAnalysisResult(
        projects=[
            ProjectAnalysis(
                title="Titanic Bootcamp",
                ai_depth_level="basic_api",
                is_thin_wrapper=False,
                is_tutorial_clone=True,
                evidence="Generic tutorial clone."
            )
        ]
    )
    penalties, reasons = calculate_penalties(llm_result)
    assert penalties >= 5
    assert any("Tutorial project penalty" in r for r in reasons)

def test_crewai_in_skills_without_project_does_not_receive_top_ai_score():
    """Skills: CrewAI + shallow/non-AI project evidence must NOT receive 36-40 points."""
    from scorer import score_ai_depth
    candidate = ExtractedCandidate(
        file_name="crewai_skills_only.pdf",
        name="George White",
        matched_skills=["Python", "CrewAI"],
        raw_text="""
        SKILLS: Python, CrewAI, Git
        PROJECTS:
        Personal Expense Tracker
        Built a simple desktop app using Python and Tkinter to track monthly expenses.
        """
    )
    # Semantic analysis indicates no AI project / none
    llm_result = LLMAnalysisResult(
        projects=[
            ProjectAnalysis(
                title="Personal Expense Tracker",
                ai_depth_level="none",
                is_ai_related=False,
                evidence="Desktop expense tracker without AI."
            )
        ]
    )
    score, evidence = score_ai_depth(candidate, llm_result)
    assert score <= 5
    assert score < 36
    assert "capped at 5/40" in evidence

def test_python_backend_skills_only_does_not_receive_max_score():
    """Skills: Python, FastAPI, PostgreSQL, Redis without project evidence must NOT receive 30/30."""
    from scorer import score_python_backend
    candidate = ExtractedCandidate(
        file_name="backend_skills_only.pdf",
        name="Hannah Green",
        matched_skills=["Python", "FastAPI", "PostgreSQL", "Redis"],
        raw_text="""
        SKILLS: Python, FastAPI, PostgreSQL, Redis, HTML, CSS
        EXPERIENCE & PROJECTS:
        Front-end Web Intern
        - Designed company marketing landing pages using HTML and CSS.
        - Wrote Python automation scripts to convert CSV data.
        """
    )
    score, evidence = score_python_backend(candidate)
    assert score < 30
    assert score <= 18
    assert "skills-only" in evidence.lower()
