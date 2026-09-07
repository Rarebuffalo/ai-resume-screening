import logging
import json
import re
from typing import List, Optional
from config import settings
from models import ExtractedCandidate, LLMAnalysisResult, ProjectAnalysis
from extractor import extract_project_sections

logger = logging.getLogger(__name__)

# Heuristic Fallback Analyzer when LLM is unavailable or fails
def fallback_heuristic_analysis(candidate: ExtractedCandidate) -> LLMAnalysisResult:
    """
    Deterministic rule-based project analyzer.
    Ensures the pipeline can run completely offline, with zero external keys or during network outages.
    """
    text_lower = candidate.raw_text.lower()
    matched = set(candidate.matched_skills)
    projects: List[ProjectAnalysis] = []
    strengths: List[str] = []
    concerns: List[str] = []

    # Detect AI Depth Level & Architecture
    is_autonomous = bool(
        {"LangGraph", "Multi-Agent", "Tool Calling", "CrewAI", "AutoGen"}.intersection(matched) or
        re.search(r"\b(?:multi[\s-]agent|langgraph|agentic\s+workflow|autonomous\s+agent)\b", text_lower)
    )
    is_rag = bool(
        {"RAG", "LlamaIndex", "ChromaDB", "Pinecone", "Qdrant", "Weaviate", "Vector Search", "Embeddings"}.intersection(matched) or
        re.search(r"\b(?:rag|retrieval[\s-]augmented|vector\s+search|embeddings?)\b", text_lower)
    )
    is_langchain = "LangChain" in matched or "langchain" in text_lower
    is_basic_api = "OpenAI API" in matched or re.search(r"\b(?:openai\s+api|gpt-?\d?[\s-]api|llm\s+api\s+call)\b", text_lower)

    # Detect Thin Wrapper
    # Indicators: mentions openai/api call, but has NO rag, no vector store, no state, no tools, no fastapi/async backend
    has_custom_backend = bool({"FastAPI", "PostgreSQL", "Redis", "AsyncIO", "Docker"}.intersection(matched))
    has_orchestration_or_data = is_autonomous or is_rag or "SQLAlchemy" in matched or "Celery" in matched
    
    is_thin_wrapper = False
    if is_basic_api and not has_orchestration_or_data and not has_custom_backend:
        is_thin_wrapper = True
    elif re.search(r"\b(?:simple\s+wrapper|wrapper\s+around\s+openai|just\s+calls?\s+the\s+api)\b", text_lower):
        is_thin_wrapper = True

    # Detect Tutorial Projects
    is_tutorial = bool(re.search(
        r"\b(?:titanic\s+survival|iris\s+dataset|mnist\s+digit|youtube\s+summarizer\s+tutorial|10-line\s+chatbot)\b",
        text_lower
    ))

    # Formulate Primary AI Project
    if is_autonomous:
        ai_depth = "autonomous_agent"
        summary = "Architected a multi-agent / stateful agentic system with tool calling and orchestration."
        evidence = "Identified stateful or agentic orchestration in candidate profile (e.g. LangGraph / Multi-Agent / Tool Calling)."
        strengths.append("Demonstrates practical multi-agent / agentic workflow architecture")
    elif is_rag:
        ai_depth = "rag_retrieval"
        summary = "Implemented a Retrieval-Augmented Generation (RAG) pipeline with vector database integration."
        evidence = "Evidence of vector embeddings and document retrieval pipeline."
        strengths.append("Practical experience with vector search and RAG retrieval pipelines")
    elif is_langchain or is_basic_api:
        ai_depth = "basic_api"
        summary = "Integrated LLM API completions and prompt chaining."
        evidence = "Uses LLM API calls with standard prompt templates."
        if is_thin_wrapper:
            concerns.append("AI project appears to be a thin LLM API wrapper lacking custom orchestration or data pipelines")
    else:
        ai_depth = "none"
        summary = "Standard software engineering project."
        evidence = "No major AI implementation identified."

    # Backend Strengths & Concerns
    if "FastAPI" in matched and ("PostgreSQL" in matched or "Redis" in matched):
        strengths.append("Strong async backend engineering with FastAPI and relational/caching datastores")
    elif "Python" in matched and not ("FastAPI" in matched or "Django" in matched or "Flask" in matched):
        concerns.append("Python usage appears limited to scripts or data tasks rather than production backend APIs")

    if is_tutorial:
        concerns.append("Project shows characteristics of standard tutorial/coursework exercises")

    if "Docker" in matched or "GCP" in matched or "AWS" in matched:
        strengths.append("Hands-on containerization and cloud deployment exposure")

    project = ProjectAnalysis(
        title="AI / Software Engineering Project",
        summary=summary,
        technologies=list(matched),
        ai_depth_level=ai_depth,
        is_thin_wrapper=is_thin_wrapper,
        is_tutorial_clone=is_tutorial,
        evidence=evidence
    )
    projects.append(project)

    overall_summary = summary
    if has_custom_backend:
        overall_summary += " Backed by custom backend engineering."

    return LLMAnalysisResult(
        projects=projects,
        strengths=strengths[:3],
        concerns=concerns[:2],
        overall_project_summary=overall_summary
    )

def analyze_with_gemini(candidate: ExtractedCandidate) -> Optional[LLMAnalysisResult]:
    """
    Calls Google Gemini using the official google-genai client with structured Pydantic response schema.
    """
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        project_text = extract_project_sections(candidate.raw_text)

        prompt = f"""
Analyze the candidate's resume excerpt below.
Focus on understanding their engineering depth, AI projects, backend skills, and whether any AI project is merely a thin API wrapper or tutorial clone.

Candidate Name: {candidate.name}
Matched Skills: {', '.join(candidate.matched_skills)}

Resume Excerpt:
\"\"\"{project_text}\"\"\"

Instructions:
1. For each significant project:
   - Identify title and technologies used.
   - Set ai_depth_level to one of: 'autonomous_agent' (multi-agent, tools, state, evaluation), 'rag_retrieval' (vector search, chunking, embeddings, RAG), 'basic_api' (simple prompt/API calls), or 'none'.
   - Flag is_thin_wrapper = True ONLY if an AI project is a superficial API call without custom retrieval, tools, state, evaluation, or backend logic.
   - Flag is_tutorial_clone = True if it is an uncustomized generic tutorial (e.g. Titanic, standard 10-line tutorial).
   - Provide concrete evidence from the text.
2. List 2-3 genuine technical strengths.
3. List 1-2 realistic technical concerns or gaps.
4. Provide a 1-sentence overall project summary.
"""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LLMAnalysisResult,
                temperature=0.1,
            ),
        )

        if response and response.text:
            parsed_data = json.loads(response.text)
            return LLMAnalysisResult(**parsed_data)

    except Exception as e:
        logger.warning(f"Gemini API call failed for {candidate.name} ({candidate.file_name}): {e}. Falling back to heuristic analysis.")
        return None

    return None

def analyze_candidate_projects(candidate: ExtractedCandidate) -> LLMAnalysisResult:
    """
    Main entry point for semantic project analysis.
    Attempts Gemini analysis first if API key is present; transparently falls back to heuristic analysis.
    Guarantees that no LLM failure can halt the batch.
    """
    if settings.GEMINI_API_KEY:
        result = analyze_with_gemini(candidate)
        if result is not None:
            return result
            
    return fallback_heuristic_analysis(candidate)
