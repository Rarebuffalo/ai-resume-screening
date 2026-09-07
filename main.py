import argparse
import sys
import logging
from pathlib import Path
from pipeline import process_resume_batch
from reporter import save_results_json, print_cli_summary

def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Resume Screening & Ranking System — Production-minded CLI for screening candidate resumes."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="./resumes",
        help="Path to folder containing PDF resumes to process (default: ./resumes)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output/results.json",
        help="Path to save output results.json (default: ./output/results.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed debug/info logging during execution"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    input_dir = Path(args.input)
    output_path = Path(args.output)

    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting resume screening pipeline...")
    print(f"  Input Directory:  {input_dir.resolve()}")
    print(f"  Output Path:      {output_path.resolve()}")

    try:
        results = process_resume_batch(input_dir)
        save_results_json(results, output_path)
        print_cli_summary(results)
        print(f"Screening complete. Results written to: {output_path.resolve()}")
    except Exception as e:
        print(f"Fatal error running screening pipeline: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
