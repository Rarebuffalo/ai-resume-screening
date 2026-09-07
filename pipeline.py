import logging
from pathlib import Path
from typing import List
from models import (
    ExtractedCandidate,
    CandidateResult,
    BatchSummary,
    ScreeningOutput
)
from parsers import parse_pdf, parse_docx
from extractor import extract_candidate_info
from eligibility import check_eligibility
from llm_client import analyze_candidate_projects
from github_client import enrich_github_profile
from scorer import compute_candidate_score

import hashlib
import re

logger = logging.getLogger(__name__)

def process_resume_batch(input_dir: Path) -> ScreeningOutput:
    """
    Main pipeline orchestrating resume screening and ranking.
    Ensures that a failure on any individual resume never halts the complete batch.
    """
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    # Discover all supported resume files (PDF and DOCX, case-insensitive)
    resume_files = sorted([
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".pdf", ".docx")
    ])
    
    total_resumes = len(resume_files)
    successfully_parsed = 0
    failed_or_unreadable = 0
    duplicates_count = 0
    seen_hashes: dict[str, str] = {}
    
    eligible_results: List[CandidateResult] = []
    rejected_results: List[CandidateResult] = []

    for file_path in resume_files:
        try:
            # 1. Resilient Document Parsing (PDF or DOCX)
            if file_path.suffix.lower() == ".docx":
                candidate = parse_docx(file_path)
            else:
                candidate = parse_pdf(file_path)
            
            if candidate.parse_error:
                failed_or_unreadable += 1
                rejected_results.append(CandidateResult(
                    candidate_name=candidate.name,
                    file_name=candidate.file_name,
                    eligible=False,
                    rejection_reasons=[f"Unreadable file: {candidate.parse_error}"],
                    matched_skills=[]
                ))
                continue

            # 2. SHA-256 Duplicate Resume Detection
            norm_text = re.sub(r"\s+", " ", candidate.raw_text).strip().lower()
            text_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()

            if text_hash in seen_hashes:
                orig_file = seen_hashes[text_hash]
                duplicates_count += 1
                rejected_results.append(CandidateResult(
                    candidate_name=candidate.name,
                    file_name=candidate.file_name,
                    eligible=False,
                    rejection_reasons=[f"Duplicate resume detected; identical to {orig_file}"],
                    matched_skills=[]
                ))
                continue

            seen_hashes[text_hash] = candidate.file_name
            successfully_parsed += 1

            # 3. Information & Skills Extraction
            candidate = extract_candidate_info(candidate)

            # 4. Deterministic Eligibility Check
            eligibility = check_eligibility(candidate)

            if not eligibility.is_eligible:
                rejected_results.append(CandidateResult(
                    candidate_name=candidate.name,
                    file_name=candidate.file_name,
                    eligible=False,
                    rejection_reasons=eligibility.rejection_reasons,
                    matched_skills=candidate.matched_skills
                ))
                continue

            # 4. Semantic Project Analysis (LLM or Heuristic Fallback)
            llm_result = analyze_candidate_projects(candidate)

            # 5. Lightweight GitHub Enrichment
            github_result = enrich_github_profile(candidate.github_username)

            # 6. Deterministic 100-Point Scoring & Penalties
            total_score, score_breakdown = compute_candidate_score(candidate, llm_result, github_result)

            eligible_results.append(CandidateResult(
                candidate_name=candidate.name,
                file_name=candidate.file_name,
                eligible=True,
                total_score=total_score,
                score_breakdown=score_breakdown,
                matched_skills=candidate.matched_skills,
                project_summary=llm_result.overall_project_summary,
                github_summary=github_result.summary,
                strengths=llm_result.strengths,
                concerns=llm_result.concerns
            ))

        except Exception as e:
            logger.error(f"Unexpected error processing {file_path.name}: {e}", exc_info=True)
            failed_or_unreadable += 1
            rejected_results.append(CandidateResult(
                candidate_name=file_path.stem,
                file_name=file_path.name,
                eligible=False,
                rejection_reasons=[f"System error: {str(e)}"],
                matched_skills=[]
            ))

    # 7. Ranking Eligible Candidates with Deterministic Tie-Breaking
    # Sorting tuple: (-total_score, -ai_depth, -python_backend, -eng_depth, -github, name)
    eligible_results.sort(
        key=lambda c: (
            -(c.total_score or 0),
            -(c.score_breakdown.ai_project_depth if c.score_breakdown else 0),
            -(c.score_breakdown.python_backend if c.score_breakdown else 0),
            -(c.score_breakdown.engineering_depth if c.score_breakdown else 0),
            -(c.score_breakdown.github if c.score_breakdown else 0),
            c.candidate_name.lower()
        )
    )

    # Assign 1-indexed ranks
    for rank_idx, cand in enumerate(eligible_results, start=1):
        cand.rank = rank_idx

    batch_summary = BatchSummary(
        total_resumes=total_resumes,
        successfully_parsed=successfully_parsed,
        eligible=len(eligible_results),
        rejected=len(rejected_results),
        failed_or_unreadable=failed_or_unreadable,
        duplicates=duplicates_count
    )

    return ScreeningOutput(
        batch_summary=batch_summary,
        ranked_candidates=eligible_results,
        rejected_candidates=rejected_results
    )
