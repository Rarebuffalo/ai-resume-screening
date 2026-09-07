from typing import Tuple, Dict, List
from config import settings
from models import ExtractedCandidate, LLMAnalysisResult, GitHubResult, ScoreBreakdown

import re
from extractor import extract_project_sections

def score_ai_depth(candidate: ExtractedCandidate, llm_result: LLMAnalysisResult) -> Tuple[int, str]:
    """
    Score AI / Agentic / RAG Project Depth (0–40).
    Rewards real AI systems: agents, RAG, tools, retrieval, state, orchestration, and evaluation.
    Keyword-only mentions in skills without project evidence are capped at 5 points.
    """
    matched = set(candidate.matched_skills)
    
    # Check project analysis level from semantic analysis
    ai_projects = [p for p in llm_result.projects if p.is_ai_related or p.ai_depth_level != "none"]
    primary_project = ai_projects[0] if ai_projects else None
    depth_level = primary_project.ai_depth_level if primary_project else "none"
    
    # 1. Advanced: Autonomous Agents / Multi-Agent / LangGraph / Tool Calling demonstrated in projects
    if depth_level == "autonomous_agent":
        score = 36
        if "LangGraph" in matched and "Tool Calling" in matched:
            score = 40
        evidence = primary_project.evidence if primary_project and primary_project.evidence else "Demonstrated stateful agentic workflows with tool calling and multi-agent coordination."
        return score, evidence

    # 2. Intermediate: Practical RAG / Vector DB / Embeddings / LlamaIndex in projects
    if depth_level == "rag_retrieval":
        score = 26
        if {"ChromaDB", "Pinecone", "Qdrant"}.intersection(matched):
            score = 28
        evidence = primary_project.evidence if primary_project and primary_project.evidence else "Practical RAG pipeline implementation with vector search and document retrieval."
        return score, evidence

    # 3. Basic: LangChain / Basic API / Prompt Chaining in projects
    if depth_level == "basic_api":
        score = 15
        evidence = primary_project.evidence if primary_project and primary_project.evidence else "LLM integration using prompt templates and API completions."
        return score, evidence

    # 4. Skills-only framework mentions with NO meaningful project evidence
    ai_skills = {"LangGraph", "LangChain", "LlamaIndex", "CrewAI", "AutoGen", "RAG", "Vector Search", "ChromaDB", "Pinecone", "OpenAI API"}.intersection(matched)
    if ai_skills:
        return 5, f"AI framework(s) listed in skills ({', '.join(sorted(ai_skills))}) without meaningful project architecture evidence (capped at 5/40)."

    return 0, "No significant AI/agentic project architecture identified."

def score_python_backend(candidate: ExtractedCandidate) -> Tuple[int, str]:
    """
    Score Python & Backend Engineering (0–30).
    Rewards Python, FastAPI, async programming, PostgreSQL, Redis in projects/internships
    over keyword-only skill lists. Project evidence carries primary weight.
    """
    matched = set(candidate.matched_skills)
    proj_text_lower = extract_project_sections(candidate.raw_text).lower()
    
    has_fastapi = "FastAPI" in matched
    has_async = "AsyncIO" in matched
    has_postgres = "PostgreSQL" in matched
    has_redis = "Redis" in matched
    has_sql = "SQLAlchemy" in matched
    has_flask_django = "Flask" in matched or "Django" in matched
    
    # Check project-level confirmation
    fastapi_in_proj = "fastapi" in proj_text_lower
    async_in_proj = "asyncio" in proj_text_lower or "async " in proj_text_lower
    postgres_in_proj = "postgres" in proj_text_lower or "postgresql" in proj_text_lower
    redis_in_proj = "redis" in proj_text_lower
    sql_in_proj = "sqlalchemy" in proj_text_lower or "sql" in proj_text_lower
    flask_django_in_proj = "flask" in proj_text_lower or "django" in proj_text_lower
    py_in_proj = "python" in proj_text_lower

    score = 0
    evidence_parts = []
    
    # 1. Base Python
    if py_in_proj:
        score += 8
        evidence_parts.append("Python project implementation")
    elif "Python" in matched:
        score += 5
        evidence_parts.append("Python skill listed")

    # 2. FastAPI & Async ecosystem (project evidence vs skills-only)
    if fastapi_in_proj and (async_in_proj or has_async):
        score += 12
        evidence_parts.append("Async FastAPI in project")
    elif fastapi_in_proj:
        score += 10
        evidence_parts.append("FastAPI in project")
    elif flask_django_in_proj:
        score += 7
        evidence_parts.append("Flask/Django in project")
    elif has_fastapi:
        score += 4
        evidence_parts.append("FastAPI (skills-only)")
    elif has_flask_django:
        score += 3
        evidence_parts.append("Flask/Django (skills-only)")

    # 3. Relational & Caching datastores (project evidence vs skills-only)
    if postgres_in_proj and redis_in_proj:
        score += 10
        evidence_parts.append("PostgreSQL & Redis datastores in project")
    elif postgres_in_proj:
        score += 6
        evidence_parts.append("PostgreSQL in project")
    elif redis_in_proj:
        score += 5
        evidence_parts.append("Redis in project")
    elif sql_in_proj:
        score += 4
        evidence_parts.append("SQLAlchemy in project")
    elif has_postgres and has_redis:
        score += 4
        evidence_parts.append("PostgreSQL & Redis (skills-only)")
    elif has_postgres:
        score += 2
        evidence_parts.append("PostgreSQL (skills-only)")
    elif has_redis:
        score += 2
        evidence_parts.append("Redis (skills-only)")
    elif has_sql:
        score += 2
        evidence_parts.append("SQLAlchemy (skills-only)")

    final_score = min(settings.WEIGHT_PYTHON_BACKEND, score)
    evidence = " + ".join(evidence_parts) if evidence_parts else "Basic Python fundamentals"
    return final_score, f"Backend engineering stack: {evidence} ({final_score}/30)."

def score_cloud_fullstack(candidate: ExtractedCandidate) -> Tuple[int, str]:
    """
    Score Cloud / Deployment / Full Stack (0–15).
    Rewards GCP, AWS, Docker, container deployment.
    React/Next.js are useful supporting signals when part of an end-to-end system.
    """
    matched = set(candidate.matched_skills)
    
    score = 0
    evidence_parts = []
    
    has_docker = "Docker" in matched
    has_k8s = "Kubernetes" in matched
    has_cloud = "GCP" in matched or "AWS" in matched or "Azure" in matched
    has_frontend = "React" in matched or "Next.js" in matched or "TypeScript" in matched
    has_cicd = "CI/CD" in matched

    if has_docker:
        score += 5
        evidence_parts.append("Docker containerization")
    if has_cloud:
        score += 5
        cloud_names = [c for c in ["GCP", "AWS", "Azure"] if c in matched]
        evidence_parts.append(f"Cloud infrastructure ({', '.join(cloud_names)})")
    if has_k8s or has_cicd:
        score += 2
        evidence_parts.append("CI/CD or orchestration")
    if has_frontend:
        score += 3
        fe_names = [f for f in ["Next.js", "React", "TypeScript"] if f in matched]
        evidence_parts.append(f"Modern frontend integration ({', '.join(fe_names)})")

    final_score = min(settings.WEIGHT_CLOUD_FULLSTACK, score)
    evidence = ", ".join(evidence_parts) if evidence_parts else "No deployment/full-stack signals detected"
    return final_score, f"{evidence} ({final_score}/15)."

def score_engineering_depth(candidate: ExtractedCandidate) -> Tuple[int, str]:
    """
    Score Engineering Depth Signals (0–5).
    Rewards testing (pytest), caching, queues, observability, concurrency, failure handling.
    """
    matched = set(candidate.matched_skills)
    
    signals = []
    score = 0
    
    if "Pytest" in matched:
        score += 2
        signals.append("Automated testing with Pytest")
    if "Caching" in matched or "Redis" in matched:
        score += 1
        signals.append("Caching strategies")
    if "Message Queues" in matched or "Celery" in matched:
        score += 1
        signals.append("Asynchronous task queues")
    if "Observability" in matched or "AsyncIO" in matched:
        score += 1
        signals.append("Concurrency & observability")

    final_score = min(settings.WEIGHT_ENGINEERING_DEPTH, score)
    evidence = "; ".join(signals) if signals else "Standard implementation patterns"
    return final_score, f"{evidence} ({final_score}/5)."

def calculate_penalties(llm_result: LLMAnalysisResult) -> Tuple[int, List[str]]:
    """
    Evaluates project-quality penalties:
    - Deduct 5–15 points for thin LLM/API wrappers with no meaningful workflow, data processing,
      retrieval, state management, backend logic, or evaluation.
    - Deduct points for tutorial-style projects without original implementation details.
    """
    penalties = 0
    reasons = []
    
    for project in llm_result.projects:
        if project.is_thin_wrapper:
            deduction = settings.PENALTY_THIN_WRAPPER_DEFAULT  # 10 points
            penalties += deduction
            reasons.append(f"Thin LLM/API wrapper penalty (-{deduction} pts): superficial API call without orchestration/retrieval/state.")
        elif project.is_tutorial_clone:
            deduction = settings.PENALTY_TUTORIAL_PROJECT      # 5 points
            penalties += deduction
            reasons.append(f"Tutorial project penalty (-{deduction} pts): project appears to be a standard generic tutorial clone.")

    # Cap maximum total penalties to 25 to prevent absurd negative overflows before clamping
    return min(25, penalties), reasons

def compute_candidate_score(
    candidate: ExtractedCandidate,
    llm_result: LLMAnalysisResult,
    github_result: GitHubResult
) -> Tuple[int, ScoreBreakdown]:
    """
    Calculates the 100-point explainable scoring model with deterministic penalty deductions.
    Returns (clamped_total_score, score_breakdown).
    """
    # 1. Category Scores
    ai_score, ai_evidence = score_ai_depth(candidate, llm_result)
    py_score, py_evidence = score_python_backend(candidate)
    cloud_score, cloud_evidence = score_cloud_fullstack(candidate)
    github_score = github_result.total_score
    eng_score, eng_evidence = score_engineering_depth(candidate)

    # 2. Penalties
    penalty_total, penalty_reasons = calculate_penalties(llm_result)

    # 3. Sum & Clamp
    raw_total = ai_score + py_score + cloud_score + github_score + eng_score
    final_score = max(0, min(100, raw_total - penalty_total))

    evidence_map = {
        "ai_project_depth": ai_evidence,
        "python_backend": py_evidence,
        "cloud_fullstack": cloud_evidence,
        "github": github_result.summary,
        "engineering_depth": eng_evidence,
    }
    if penalty_reasons:
        evidence_map["penalties"] = " | ".join(penalty_reasons)

    breakdown = ScoreBreakdown(
        ai_project_depth=ai_score,
        python_backend=py_score,
        cloud_fullstack=cloud_score,
        github=github_score,
        engineering_depth=eng_score,
        penalties_applied=penalty_total,
        evidence_map=evidence_map
    )

    return final_score, breakdown
