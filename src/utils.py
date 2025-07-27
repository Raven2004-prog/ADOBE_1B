# src/utils.py

import os
import glob
import re
import json
import fitz  # PyMuPDF


def load_input_spec(spec_path):
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_task1a_outputs(outputs_dir):
    outputs = {}
    for filepath in glob.glob(os.path.join(outputs_dir, '*.json')):
        key = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            outputs[key] = json.load(f)
    return outputs


def write_output1b(result_dict, output_path):
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)


def _normalize_stem(name: str) -> str:
    stem = os.path.splitext(name)[0]
    return re.sub(r'[^0-9a-zA-Z]+', '', stem).lower()


def extract_section_body(section_list, input_pdf_dir):
    """
    For each section in `section_list` (global importance order), finds its in-document successor,
    then extracts only the text between them. Returns list of dicts with keys:
      - document
      - refined_text
      - page_number
    """
    # Build exact and normalized filename maps
    pdf_map_exact = {
        os.path.basename(p): p
        for p in glob.glob(os.path.join(input_pdf_dir, '*.pdf'))
    }
    pdf_map_norm = {
        _normalize_stem(name): path
        for name, path in pdf_map_exact.items()
    }

    # 1) Annotate each valid section with page_idx & y_start
    valid_secs = []
    for sec in section_list:
        doc_name = sec.get('document')
        # Locate PDF path
        pdf_path = pdf_map_exact.get(doc_name) or pdf_map_norm.get(_normalize_stem(doc_name))
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"[DEBUG] ❌ PDF not found for section {doc_name!r}")
            continue

        # Resolve page_number (try both keys)
        page_n = sec.get('page_number')
        if page_n is None:
            page_n = sec.get('page')
        if page_n is None:
            print(f"[DEBUG] ⚠ missing page_number for section {doc_name!r} / {sec.get('section_title')!r}; skipping")
            continue

        # Convert 1-based to 0-based index
        page_idx = page_n - 1

        # Open PDF & validate page_idx
        doc = fitz.open(pdf_path)
        if page_idx < 0 or page_idx >= doc.page_count:
            print(f"[DEBUG] ⚠ invalid page_idx={page_idx} for {doc_name!r} (has {doc.page_count} pages)")
            doc.close()
            continue

        # Find y_start on this page
        pg = doc[page_idx]
        rects = pg.search_for(sec.get('section_title', ''))
        y_start = rects[0].y1 if rects else 0.0
        doc.close()

        # Annotate and collect
        sec['_pdf_path'] = pdf_path
        sec['_page_idx'] = page_idx
        sec['y_start']   = y_start
        valid_secs.append(sec)

    # 2) Group & sort within each document
    from collections import defaultdict
    doc_groups = defaultdict(list)
    for sec in valid_secs:
        doc_groups[sec['document']].append(sec)
    for group in doc_groups.values():
        group.sort(key=lambda s: (s['_page_idx'], s['y_start']))

    # 3) Extract bodies between each heading and its successor
    results = []
    for sec in valid_secs:
        fname    = sec['document']
        page_n   = sec.get('page_number') or sec.get('page')
        page_idx = sec['_page_idx']
        y0       = sec['y_start']
        pdf_path = sec['_pdf_path']

        group    = doc_groups[fname]
        idx      = group.index(sec)
        next_sec = group[idx + 1] if idx + 1 < len(group) else None

        # Determine same-page clip
        y1 = None
        if next_sec and next_sec['_page_idx'] == page_idx:
            y1 = next_sec['y_start']

        doc = fitz.open(pdf_path)
        body_lines = []

        # Current page slice
        pg = doc[page_idx]
        for block in pg.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                y = line['bbox'][1]
                if y < y0 or (y1 is not None and y >= y1):
                    continue
                t = ' '.join(span['text'] for span in line['spans']).strip()
                if t:
                    body_lines.append(t)

        # Intermediate pages
        if next_sec and next_sec['_page_idx'] > page_idx:
            next_idx = next_sec['_page_idx']
            for pno in range(page_idx + 1, next_idx):
                pg2 = doc[pno]
                for block in pg2.get_text('dict')['blocks']:
                    for line in block.get('lines', []):
                        t = ' '.join(span['text'] for span in line['spans']).strip()
                        if t:
                            body_lines.append(t)
            # Clip on next page
            pgn = doc[next_idx]
            y_end = next_sec['y_start']
            for block in pgn.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    y = line['bbox'][1]
                    if y >= y_end:
                        continue
                    t = ' '.join(span['text'] for span in line['spans']).strip()
                    if t:
                        body_lines.append(t)

        doc.close()
        refined = ' '.join(body_lines)
        results.append({
            "document":     fname,
            "refined_text": refined,
            "page_number":  page_n
        })

    return results
