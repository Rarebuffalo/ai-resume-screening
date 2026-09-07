from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProjectAnalysis(BaseModel):
    title: str = Field(default="", description="Name or title of project")
    summary: str = Field(default="", description="Summary of project architecture and implementation")
    technologies: List[str] = Field(default_factory=list, description="Technologies and libraries used")
    ai_depth_level: str = Field(default="none", description="One of: 'autonomous_agent', 'rag_retrieval', 'basic_api', 'none'")
    is_ai_related: bool = Field(default=False, description="Whether project involves AI/LLM/RAG/agents")
    is_thin_wrapper: bool = Field(default=False, description="True if the project is merely a superficial API call without orchestration/retrieval/state")
    is_tutorial_clone: bool = Field(default=False, description="True if project looks like a standard uncustomized tutorial or toy project")
    evidence: str = Field(default="", description="Specific evidence showing depth or thinness")

class LLMAnalysisResult(BaseModel):
    projects: List[ProjectAnalysis] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    overall_project_summary: str = Field(default="")

class ExtractedCandidate(BaseModel):
    file_name: str
    name: str = "Unknown Candidate"
    email: str = "Not provided"
    github_url: Optional[str] = None
    github_username: Optional[str] = None
    matched_skills: List[str] = Field(default_factory=list)
    raw_text: str = ""
    parse_error: Optional[str] = None

class EligibilityResult(BaseModel):
    is_eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    has_python_evidence: bool = False
    has_ai_evidence: bool = False
    python_evidence: str = ""
    ai_evidence: str = ""

class ScoreBreakdown(BaseModel):
    ai_project_depth: int = Field(default=0, ge=0, le=40)
    python_backend: int = Field(default=0, ge=0, le=30)
    cloud_fullstack: int = Field(default=0, ge=0, le=15)
    github: int = Field(default=0, ge=0, le=10)
    engineering_depth: int = Field(default=0, ge=0, le=5)
    penalties_applied: int = 0
    evidence_map: Dict[str, str] = Field(default_factory=dict)

class GitHubResult(BaseModel):
    username: Optional[str] = None
    activity_score: int = Field(default=0, ge=0, le=5)
    repo_score: int = Field(default=0, ge=0, le=5)
    total_score: int = Field(default=0, ge=0, le=10)
    status: str = "skipped"  # success, rate_limited, not_found, skipped, error
    summary: str = "GitHub enrichment skipped"

class CandidateResult(BaseModel):
    rank: Optional[int] = None
    candidate_name: str
    file_name: str
    eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    total_score: Optional[int] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    matched_skills: List[str] = Field(default_factory=list)
    project_summary: str = ""
    github_summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)

class BatchSummary(BaseModel):
    total_resumes: int = 0
    successfully_parsed: int = 0
    eligible: int = 0
    rejected: int = 0
    failed_or_unreadable: int = 0
    duplicates: int = 0

class ScreeningOutput(BaseModel):
    batch_summary: BatchSummary
    ranked_candidates: List[CandidateResult] = Field(default_factory=list)
    rejected_candidates: List[CandidateResult] = Field(default_factory=list)
