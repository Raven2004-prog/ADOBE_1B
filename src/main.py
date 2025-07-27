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
from utils import (
    load_input_spec,
    load_task1a_outputs,
    write_output1b,
    extract_section_body
)
from relevance import filter_headings


def main():
    parser = argparse.ArgumentParser(
        description="Task 1B: Filter Task 1A headings by relevance to persona & job."
    )
    parser.add_argument("--input", dest="pdf_dir",
                        default=DEFAULT_INPUT_PDF_DIR,
                        help="Folder containing PDFs")
    parser.add_argument("--task1a", dest="task1a_dir",
                        default=DEFAULT_TASK1A_OUTPUT_DIR,
                        help="Folder containing Task 1A JSON outputs")
    parser.add_argument("--input-spec", dest="spec_file",
                        default=DEFAULT_INPUT_SPEC_FILE,
                        help="Path to challenge1b_input.json")
    parser.add_argument("--output", dest="output_file",
                        default=DEFAULT_OUTPUT_FILE,
                        help="Path to write output1b.json")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Optional similarity cutoff override")
    args = parser.parse_args()

    # 1) load spec and 1A outputs
    raw_spec       = load_input_spec(args.spec_file)
    input_spec     = {
        "persona":        raw_spec["persona"]["role"],
        "job_to_be_done": raw_spec["job_to_be_done"]["task"],
    }
    task1a_outputs = load_task1a_outputs(args.task1a_dir)
    threshold      = args.threshold if args.threshold is not None else DEFAULT_THRESHOLD

    # 2) get relevance scores
    relevant = filter_headings(input_spec, task1a_outputs, threshold)

    # 3) metadata
    metadata = {
        "input_documents":     [d["filename"] for d in raw_spec["documents"]],
        "persona":             input_spec["persona"],
        "job_to_be_done":      input_spec["job_to_be_done"],
        "processing_timestamp": datetime.now().isoformat(),
    }

    # 4) flatten & globally rank headings
    title_to_filename = {d["title"]: d["filename"] for d in raw_spec["documents"]}
    all_hits = []
    for title, heads in relevant.items():
        fname = title_to_filename.get(title, f"{title}.pdf")
        for h in heads:
            all_hits.append({
                "document":      fname,
                "section_title": h["text"].strip(),
                "page_number":   h.get("page") or h.get("page_number"),
                "score":         h["score"]
            })
    all_hits.sort(key=lambda x: x["score"], reverse=True)

    # 5) build extracted_sections (only desired keys)
    clean_sections = []
    for rank, hit in enumerate(all_hits, start=1):
        clean_sections.append({
            "document":        hit["document"],
            "section_title":   hit["section_title"],
            "importance_rank": rank,
            "page_number":     hit["page_number"]
        })

    # 6) subsection analysis
    section_meta = [sec.copy() for sec in clean_sections]
    subsection_analysis = extract_section_body(
        section_meta,
        args.pdf_dir
    )

    # 7) final output
    output = {
        "metadata":            metadata,
        "extracted_sections":  clean_sections,
        "subsection_analysis": subsection_analysis
    }
    write_output1b(output, args.output_file)
    print(f"Wrote Task 1B output to {args.output_file}")


if __name__ == "__main__":
    main()
