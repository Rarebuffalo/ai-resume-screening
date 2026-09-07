import pytest
from pathlib import Path
from parsers import parse_pdf
from extractor import extract_email, extract_github, extract_candidate_name

def test_malformed_pdf_does_not_crash(tmp_path):
    corrupt_file = tmp_path / "corrupted.pdf"
    corrupt_file.write_bytes(b"NOT A REAL PDF CONTENT RANDOM BYTES")
    
    candidate = parse_pdf(corrupt_file)
    assert candidate.parse_error is not None
    assert "PDF parsing error" in candidate.parse_error
    assert candidate.raw_text == ""

def test_empty_pdf_handled(tmp_path):
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")

    candidate = parse_pdf(empty_file)
    assert candidate.parse_error is not None
    assert "empty" in candidate.parse_error.lower()

def test_contact_info_extraction():
    sample_text = """
    Asha Rao
    asha.rao.dev@gmail.com | +91-9876543210 | github.com/asharao-tech
    Software Engineer with expertise in Python and LangGraph.
    """
    email = extract_email(sample_text)
    assert email == "asha.rao.dev@gmail.com"

    url, username = extract_github(sample_text)
    assert url == "https://github.com/asharao-tech"
    assert username == "asharao-tech"

    name = extract_candidate_name(sample_text, "candidate_asha.pdf")
    assert name == "Asha Rao"

def test_duplicate_resume_detection(tmp_path):
    """Verifies that duplicate resumes with different filenames are detected and only scored once."""
    from generate_sample_resumes import create_pdf
    from pipeline import process_resume_batch

    lines = [
        "Asha Rao",
        "asha@example.com",
        "SKILLS: Python, FastAPI, LangGraph, PostgreSQL",
        "PROJECTS: Autonomous agent pipeline using LangGraph and Python FastAPI."
    ]
    
    file1 = tmp_path / "resume_1.pdf"
    file2 = tmp_path / "resume_1_copy.pdf"
    create_pdf(file1, lines)
    create_pdf(file2, lines)

    results = process_resume_batch(tmp_path)
    assert results.batch_summary.total_resumes == 2
    assert results.batch_summary.duplicates == 1
    assert results.batch_summary.eligible == 1
    assert len(results.ranked_candidates) == 1
    assert results.ranked_candidates[0].candidate_name == "Asha Rao"
    assert any("Duplicate resume detected" in r for cand in results.rejected_candidates for r in cand.rejection_reasons)
