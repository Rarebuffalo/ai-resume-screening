import re
from pathlib import Path
from typing import List, Optional, Tuple, Set
from models import ExtractedCandidate

# Standard skill catalog for regex matching
SKILLS_TAXONOMY = {
    # Python & Backend
    "Python": r"\bpython(?:3)?\b",
    "FastAPI": r"\bfastapi\b",
    "Flask": r"\bflask\b",
    "Django": r"\bdjango\b",
    "PostgreSQL": r"\bpostgres(?:ql)?\b",
    "Redis": r"\bredis\b",
    "SQLAlchemy": r"\bsqlalchemy\b",
    "AsyncIO": r"\basyncio\b",
    "Celery": r"\bcelery\b",
    
    # AI / Agentic / RAG
    "LangChain": r"\blangchain\b",
    "LangGraph": r"\blanggraph\b",
    "LlamaIndex": r"\bllamaindex\b",
    "Google ADK": r"\b(?:google\s+adk|agent\s+development\s+kit)\b",
    "CrewAI": r"\bcrewai\b",
    "AutoGen": r"\bautogen\b",
    "RAG": r"\b(?:rag|retrieval[\s-]augmented[\s-]generation)\b",
    "Vector Search": r"\b(?:vector[\s-]search|vector[\s-]database|vector[\s-]store)\b",
    "Embeddings": r"\bembeddings?\b",
    "Tool Calling": r"\b(?:tool[\s-]calling|function[\s-]calling)\b",
    "Multi-Agent": r"\b(?:multi[\s-]agent|agentic[\s-]workflow|ai[\s-]agents?)\b",
    "ChromaDB": r"\bchroma(?:db)?\b",
    "Pinecone": r"\bpinecone\b",
    "Qdrant": r"\bqdrant\b",
    "Weaviate": r"\bweaviate\b",
    "OpenAI API": r"\bopenai(?:\s+api)?\b",
    "Anthropic": r"\banthropic\b",
    
    # Cloud / Deployment / Full Stack
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "GCP": r"\b(?:gcp|google\s+cloud(?:\s+platform)?)\b",
    "AWS": r"\b(?:aws|amazon\s+web\s+services)\b",
    "Azure": r"\b(?:azure|microsoft\s+azure)\b",
    "CI/CD": r"\bci[/-]cd\b|\bgithub[\s-]actions\b",
    "React": r"\breact(?:\.js)?\b",
    "Next.js": r"\bnext(?:\.js)?\b",
    "TypeScript": r"\btypescript\b",
    "Node.js": r"\bnode(?:\.js)?\b",
    "Java": r"\bjava\b",
    "Spring Boot": r"\bspring[\s-]boot\b",
    
    # Engineering Depth
    "Pytest": r"\bpytest\b|\bunit[\s-]testing\b",
    "Caching": r"\bcaching\b|\bcache\b",
    "Message Queues": r"\b(?:message[\s-]queue|rabbitmq|kafka)\b",
    "Observability": r"\b(?:observability|prometheus|grafana|opentelemetry)\b",
}

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
GITHUB_URL_REGEX = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

# Non-user paths in github.com to filter out
GITHUB_IGNORE_USERNAMES = {"features", "pricing", "marketplace", "topics", "collections", "trending", "events", "login", "join"}

def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None

def extract_github(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract (github_url, github_username) from text."""
    matches = GITHUB_URL_REGEX.findall(text)
    for m in matches:
        username = m.strip("/").strip()
        if username.lower() not in GITHUB_IGNORE_USERNAMES and len(username) > 1:
            return f"https://github.com/{username}", username
            
    # Try pattern like "GitHub: username"
    handle_match = re.search(r"\bgithub:\s*@?([A-Za-z0-9_-]+)", text, re.IGNORECASE)
    if handle_match:
        username = handle_match.group(1).strip()
        if username.lower() not in GITHUB_IGNORE_USERNAMES and len(username) > 1:
            return f"https://github.com/{username}", username

    return None, None

def extract_candidate_name(text: str, file_name: str) -> str:
    """
    Extract candidate name from top lines of text, or fall back to cleaned filename.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Common headers to ignore
    ignore_patterns = [
        r"resume", r"curriculum\s+vitae", r"cv", r"email", r"phone", r"github",
        r"linkedin", r"education", r"experience", r"skills", r"projects", r"summary",
        r"page\s+\d+", r"contact", r"profile"
    ]
    
    for line in lines[:5]:
        line_clean = line.strip()
        # Must not contain email, phone, or url
        if EMAIL_REGEX.search(line_clean) or GITHUB_URL_REGEX.search(line_clean) or PHONE_REGEX.search(line_clean):
            continue
        if any(re.search(p, line_clean, re.IGNORECASE) for p in ignore_patterns):
            continue
        # Names typically have 2-4 words, length 3-40 chars, mostly alpha
        words = line_clean.split()
        if 1 <= len(words) <= 4 and 2 <= len(line_clean) <= 40:
            if re.match(r"^[A-Za-z\s.'-]+$", line_clean):
                return line_clean

    # Fallback to file name
    clean_fn = Path(file_name).stem
    # Remove words like "resume", "cv", numbers
    clean_fn = re.sub(r"[_\-\.]+", " ", clean_fn)
    clean_fn = re.sub(r"\b(resume|cv|draft|final|v\d+|\d+)\b", "", clean_fn, flags=re.IGNORECASE).strip()
    return clean_fn.title() if clean_fn else "Candidate"

def extract_matched_skills(text: str) -> List[str]:
    """Scan raw text for known skills with word boundary regex."""
    matched = []
    text_lower = text.lower()
    for skill_name, pattern in SKILLS_TAXONOMY.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            matched.append(skill_name)
    return matched

def extract_project_sections(text: str) -> str:
    """
    Isolate project or experience sections from the resume for targeted semantic analysis.
    If section headers are not clearly found, returns the whole text.
    """
    # Look for headers like Projects, Experience, Technical Projects
    pattern = r"(?:Projects|Technical Projects|Experience|Work Experience|Key Projects)[\s\S]*?(?:Education|Certifications|Achievements|Awards|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match and len(match.group(0)) > 100:
        return match.group(0).strip()
    return text[:2500].strip()

def extract_candidate_info(candidate: ExtractedCandidate) -> ExtractedCandidate:
    """
    Enrich an ExtractedCandidate with name, email, GitHub info, and matched skills.
    """
    if candidate.parse_error or not candidate.raw_text:
        return candidate

    text = candidate.raw_text
    candidate.name = extract_candidate_name(text, candidate.file_name)
    candidate.email = extract_email(text) or "Not provided"
    
    github_url, github_username = extract_github(text)
    candidate.github_url = github_url
    candidate.github_username = github_username
    
    candidate.matched_skills = extract_matched_skills(text)
    return candidate
