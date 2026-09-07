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

def evaluate_ai_evidence(candidate: ExtractedCandidate) -> Tuple[bool, str]:
    """
    Evaluates whether the candidate has meaningful AI/LLM/RAG/agentic evidence.
    Requires at least one recognized AI framework, RAG pipeline, agentic workflow,
    vector database, or tool-calling system.
    """
    matched = set(candidate.matched_skills)
    found_indicators = matched.intersection(AI_INDICATORS)
    
    if found_indicators:
        return True, f"AI/agentic project and framework evidence identified: {', '.join(sorted(found_indicators))}."

    # Contextual check in text for terms like 'retrieval-augmented', 'agentic workflow', 'tool calling'
    text_lower = candidate.raw_text.lower()
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

    return False, "No AI/agentic project evidence (LangChain, LangGraph, RAG, vector search, or agents)."

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
