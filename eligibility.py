import re
from typing import List, Tuple
from models import ExtractedCandidate, EligibilityResult

# Recognized Python indicators (core language and primary backend ecosystem)
PYTHON_INDICATORS = {
    "Python", "FastAPI", "Flask", "Django", "SQLAlchemy", "AsyncIO", "Celery", "Pytest"
}

# Recognized AI / Agentic / RAG indicators
AI_INDICATORS = {
    "LangChain", "LangGraph", "LlamaIndex", "Google ADK", "CrewAI", "AutoGen",
    "RAG", "Vector Search", "Embeddings", "Tool Calling", "Multi-Agent",
    "ChromaDB", "Pinecone", "Qdrant", "Weaviate", "OpenAI API", "Anthropic"
}

def evaluate_python_evidence(candidate: ExtractedCandidate) -> Tuple[bool, str]:
    """
    Evaluates whether the candidate has genuine Python evidence.
    Evidence may come from skills, project technology, work experience, or implementation details.
    """
    matched = set(candidate.matched_skills)
    
    # 1. Direct Python in matched skills or ecosystem frameworks
    found_indicators = matched.intersection(PYTHON_INDICATORS)
    if "Python" in found_indicators:
        return True, "Python identified in candidate skills and technical profile."
    if len(found_indicators) > 0:
        return True, f"Python backend ecosystem usage identified: {', '.join(sorted(found_indicators))}."

    # 2. Contextual check in raw text for Python implementation details
    text = candidate.raw_text
    python_matches = re.findall(r"\bpython(?:3)?\b", text, re.IGNORECASE)
    if python_matches:
        # Check that it is not negated (e.g. "not Python")
        return True, f"Python mentioned {len(python_matches)} time(s) in technical context."

    return False, "No evidence of Python stack found in skills, projects, or experience."

from extractor import extract_project_sections

def evaluate_ai_evidence(candidate: ExtractedCandidate) -> Tuple[bool, str]:
    """
    Evaluates whether the candidate has meaningful AI/LLM/RAG/agentic evidence.
    Requires genuine project or implementation evidence. A single bare AI keyword
    (e.g., 'LangChain' or 'OpenAI API') in a skills section without project context is rejected.
    """
    matched = set(candidate.matched_skills)
    found_indicators = matched.intersection(AI_INDICATORS)
    
    if not found_indicators:
        return False, "No AI/agentic project evidence (LangChain, LangGraph, RAG, vector search, or agents)."

    text_lower = candidate.raw_text.lower()
    proj_text_lower = extract_project_sections(candidate.raw_text).lower()

    # 1. Custom explicit architectural patterns anywhere in text
    custom_ai_patterns = [
        (r"\b(?:retrieval[\s-]augmented[\s-]generation|rag\s+pipeline)\b", "RAG pipeline implementation"),
        (r"\b(?:agentic\s+workflow|autonomous\s+agent|multi[\s-]agent)\b", "Agentic / multi-agent workflow"),
        (r"\b(?:function[\s-]calling|tool[\s-]calling\s+agent)\b", "Tool-calling agent"),
        (r"\b(?:vector\s+(?:embeddings?|similarity\s+search))\b", "Vector search & embeddings"),
        (r"\b(?:llm\s+orchestration|eval(?:uation)?\s+pipeline)\b", "LLM orchestration & evaluation"),
    ]
    
    for pattern, description in custom_ai_patterns:
        if re.search(pattern, text_lower):
            return True, f"Meaningful AI implementation found: {description}."

    # 2. Check if any AI indicator appears inside project / experience sections
    proj_ai_found = [ind for ind in found_indicators if re.search(r"\b" + re.escape(ind.lower()) + r"\b", proj_text_lower)]
    if proj_ai_found:
        return True, f"AI/agentic project implementation identified: {', '.join(sorted(proj_ai_found))}."

    # 3. Multiple cooperating AI indicators together across profile (e.g. LangChain + RAG, LangGraph + Tool Calling)
    if len(found_indicators) >= 2:
        return True, f"Multiple AI/agentic technologies identified across profile: {', '.join(sorted(found_indicators))}."

    # 4. If only 1 AI indicator was found and it only appears in skills context (not in projects)
    single_ind = list(found_indicators)[0]
    return False, f"Single AI keyword ('{single_ind}') in skills list without meaningful project or implementation context."

def check_eligibility(candidate: ExtractedCandidate) -> EligibilityResult:
    """
    Determines candidate eligibility deterministically.
    Candidates must satisfy BOTH Python evidence and AI/agentic evidence.
    Presence of Java, JavaScript, React, Next.js, etc. does NOT cause rejection.
    """
    has_python, python_evidence = evaluate_python_evidence(candidate)
    has_ai, ai_evidence = evaluate_ai_evidence(candidate)
    
    rejection_reasons: List[str] = []
    if not has_python:
        rejection_reasons.append("No evidence of Python stack")
    if not has_ai:
        rejection_reasons.append("No AI/agentic project evidence")

    is_eligible = (has_python and has_ai)

    return EligibilityResult(
        is_eligible=is_eligible,
        rejection_reasons=rejection_reasons,
        has_python_evidence=has_python,
        has_ai_evidence=has_ai,
        python_evidence=python_evidence,
        ai_evidence=ai_evidence
    )
