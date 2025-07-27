# src/main.py

import argparse
import json
from datetime import datetime

from config import (
    DEFAULT_INPUT_PDF_DIR,
    DEFAULT_TASK1A_OUTPUT_DIR,
    DEFAULT_INPUT_SPEC_FILE,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_THRESHOLD
)
from utils import load_input_spec, load_task1a_outputs, write_output1b
from relevance import filter_headings


def main():
    parser = argparse.ArgumentParser(
        description="Task 1B: Filter Task 1A headings by relevance to persona & job."
    )
    parser.add_argument(
        "--input",
        dest="pdf_dir",
        default=DEFAULT_INPUT_PDF_DIR,
        help="Directory with original PDFs (not directly used by this script)",
    )
    parser.add_argument(
        "--task1a",
        dest="task1a_dir",
        default=DEFAULT_TASK1A_OUTPUT_DIR,
        help="Directory containing Task 1A output JSON files",
    )
    parser.add_argument(
        "--input-spec",
        dest="spec_file",
        default=DEFAULT_INPUT_SPEC_FILE,
        help="Path to challenge1b_input.json",
    )
    parser.add_argument(
        "--output",
        dest="output_file",
        default=DEFAULT_OUTPUT_FILE,
        help="Where to write the Task 1B output JSON",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Optional override for cosine‐similarity cutoff",
    )
    args = parser.parse_args()

    # Load and reshape the input spec
    raw_spec = load_input_spec(args.spec_file)
    input_spec = {
        "persona": raw_spec["persona"]["role"],
        "job_to_be_done": raw_spec["job_to_be_done"]["task"],
    }

    # Load all Task 1A outputs
    task1a_outputs = load_task1a_outputs(args.task1a_dir)

    # Determine similarity threshold
    threshold = args.threshold if args.threshold is not None else DEFAULT_THRESHOLD

    # Filter headings by relevance
    relevant = filter_headings(input_spec, task1a_outputs, threshold)

    # Build metadata
    metadata = {
        "input_documents": [doc["filename"] for doc in raw_spec["documents"]],
        "persona": input_spec["persona"],
        "job_to_be_done": input_spec["job_to_be_done"],
        "processing_timestamp": datetime.now().isoformat(),
    }

    # --- Flatten & globally rank all relevant headings ---
    # Map titles back to filenames
    title_to_filename = {
        doc["title"]: doc["filename"] for doc in raw_spec["documents"]
    }

    # Collect all hits with their scores
    all_hits = []
    for title, headings in relevant.items():
        filename = title_to_filename.get(title, f"{title}.pdf")
        for h in headings:
            all_hits.append({
                "document": filename,
                "section_title": h.get("text", "").strip(),
                "page_number": h.get("page") or h.get("page_number"),
                "score": h["score"]
            })

    # Sort globally by descending score
    all_hits.sort(key=lambda x: x["score"], reverse=True)

    # Assign a single importance_rank across all docs
    extracted_sections = []
    for rank, hit in enumerate(all_hits, start=1):
        extracted_sections.append({
            "document":        hit["document"],
            "section_title":   hit["section_title"],
            "importance_rank": rank,
            "page_number":     hit["page_number"]
        })
    # --- End global ranking ---

    # Placeholder for deeper analysis
    subsection_analysis = []

    # Final output structure
    output = {
        "metadata": metadata,
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    write_output1b(output, args.output_file)
    print(f"Wrote Task 1B output to {args.output_file}")


if __name__ == "__main__":
    main()
