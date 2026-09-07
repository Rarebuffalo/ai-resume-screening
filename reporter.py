import json
from pathlib import Path
from models import ScreeningOutput

def save_results_json(screening_output: ScreeningOutput, output_path: Path) -> None:
    """
    Serializes the complete screening output into machine-readable JSON.
    Creates parent directories if necessary.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(screening_output.model_dump(), f, indent=2, ensure_ascii=False)

def print_cli_summary(screening_output: ScreeningOutput) -> None:
    """
    Prints a clean, explainable terminal report summarizing the screening batch.
    """
    summary = screening_output.batch_summary
    print("\n" + "=" * 80)
    print("           AI RESUME SCREENING & RANKING SYSTEM — BATCH SUMMARY")
    print("=" * 80)
    print(f" Total Resumes Processed:  {summary.total_resumes}")
    print(f" Successfully Parsed:      {summary.successfully_parsed}")
    print(f" Eligible Candidates:      {summary.eligible}")
    print(f" Rejected Candidates:      {summary.rejected}")
    print(f" Failed / Unreadable:      {summary.failed_or_unreadable}")
    print("-" * 80)

    print("\n[RANKED ELIGIBLE CANDIDATES]")
    if not screening_output.ranked_candidates:
        print("  No eligible candidates found matching both Python and AI requirements.")
    else:
        print(f"{'Rank':<5} | {'Candidate Name':<22} | {'Score':<6} | {'AI':<4} | {'Py':<4} | {'Cloud':<5} | {'GH':<3} | {'Eng':<3} | {'Skills'}")
        print("-" * 80)
        for c in screening_output.ranked_candidates:
            sb = c.score_breakdown
            skills_str = ", ".join(c.matched_skills[:4])
            if len(c.matched_skills) > 4:
                skills_str += f" (+{len(c.matched_skills)-4})"
            print(f"{c.rank:<5} | {c.candidate_name:<22} | {c.total_score:<6} | {sb.ai_project_depth:<4} | {sb.python_backend:<4} | {sb.cloud_fullstack:<5} | {sb.github:<3} | {sb.engineering_depth:<3} | {skills_str}")
            if sb.penalties_applied > 0:
                print(f"      * Penalty Applied: -{sb.penalties_applied} pts ({sb.evidence_map.get('penalties', '')})")

    print("\n[DISQUALIFIED / REJECTED CANDIDATES]")
    if not screening_output.rejected_candidates:
        print("  None.")
    else:
        for c in screening_output.rejected_candidates:
            reasons = "; ".join(c.rejection_reasons)
            skills = f" (Skills: {', '.join(c.matched_skills)})" if c.matched_skills else ""
            print(f"  - {c.candidate_name} ({c.file_name}): {reasons}{skills}")

    print("=" * 80 + "\n")
