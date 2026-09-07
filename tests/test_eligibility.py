from models import ExtractedCandidate
from eligibility import check_eligibility

def test_eligible_python_and_ai_candidate():
    candidate = ExtractedCandidate(
        file_name="test_candidate.pdf",
        name="Alice Kumar",
        matched_skills=["Python", "FastAPI", "LangGraph", "ChromaDB"],
        raw_text="Experienced in Python backend using FastAPI and LangGraph for agentic workflows."
    )
    result = check_eligibility(candidate)
    assert result.is_eligible is True
    assert len(result.rejection_reasons) == 0
    assert result.has_python_evidence is True
    assert result.has_ai_evidence is True

def test_reject_python_only_candidate():
    candidate = ExtractedCandidate(
        file_name="test_py_only.pdf",
        name="Bob Singh",
        matched_skills=["Python", "Django", "PostgreSQL", "Celery"],
        raw_text="Built scalable web apps in Python with Django and PostgreSQL."
    )
    result = check_eligibility(candidate)
    assert result.is_eligible is False
    assert "No AI/agentic project evidence" in result.rejection_reasons
    assert result.has_python_evidence is True
    assert result.has_ai_evidence is False

def test_reject_ai_only_no_python():
    candidate = ExtractedCandidate(
        file_name="test_ai_no_py.pdf",
        name="Charlie Brown",
        matched_skills=["LangChain", "Node.js", "TypeScript", "React"],
        raw_text="Built full-stack AI chatbot with LangChain in Node.js and TypeScript."
    )
    result = check_eligibility(candidate)
    assert result.is_eligible is False
    assert "No evidence of Python stack" in result.rejection_reasons
    assert result.has_python_evidence is False
    assert result.has_ai_evidence is True

def test_reject_java_react_only():
    candidate = ExtractedCandidate(
        file_name="test_java_react.pdf",
        name="Dave Miller",
        matched_skills=["Java", "Spring Boot", "React"],
        raw_text="Full-stack enterprise developer working with Java, Spring Boot, and React."
    )
    result = check_eligibility(candidate)
    assert result.is_eligible is False
    assert "No evidence of Python stack" in result.rejection_reasons
    assert "No AI/agentic project evidence" in result.rejection_reasons

def test_mixed_stack_with_python_and_ai_remains_eligible():
    """Candidates with Java, React, Next.js must NOT be rejected if Python + AI are satisfied."""
    candidate = ExtractedCandidate(
        file_name="test_mixed.pdf",
        name="Elena Rostova",
        matched_skills=["Java", "Spring Boot", "React", "Next.js", "Python", "FastAPI", "LangChain", "RAG"],
        raw_text="Maintained Java microservices and built new Python FastAPI RAG pipeline with React UI."
    )
    result = check_eligibility(candidate)
    assert result.is_eligible is True
    assert len(result.rejection_reasons) == 0

def test_reject_bare_langchain_keyword_in_skills_without_project():
    """Skills: Python, LangChain with no meaningful AI project/implementation -> must NOT pass AI eligibility."""
    candidate = ExtractedCandidate(
        file_name="test_bare_keyword.pdf",
        name="Frank White",
        matched_skills=["Python", "LangChain"],
        raw_text="""
        Frank White
        frank@example.com
        SKILLS
        Python, LangChain, HTML, CSS
        PROJECTS
        Personal Portfolio Website
        - Developed a personal static portfolio site using HTML and CSS.
        - Built Python script to parse personal financial spreadsheets.
        """
    )
    result = check_eligibility(candidate)
    assert result.is_eligible is False
    assert "No AI/agentic project evidence" in result.rejection_reasons
    assert result.has_python_evidence is True
    assert result.has_ai_evidence is False
