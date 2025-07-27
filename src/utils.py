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


def extract_section_body(section_list, input_pdf_dir):
    """
    For each section in `section_list` (global importance order), finds its sibling
    in-document successor, then extracts only the text between them.
    Returns list of dicts with keys: document, refined_text, page_number.
    """
    # map bare filename → full path
    pdf_map = {os.path.basename(p): p for p in glob.glob(os.path.join(input_pdf_dir, '*.pdf'))}
    # normalized map for loose matching
    norm_map = {
        re.sub(r'[^0-9a-zA-Z]+', '', name).lower(): p
        for name, p in pdf_map.items()
    }

    # 1) compute y_start for each heading
    for sec in section_list:
        fname = sec['document']
        # locate file
        pdf_path = pdf_map.get(fname) \
                   or pdf_map.get(fname.replace('_', ' ')) \
                   or norm_map.get(re.sub(r'[^0-9a-zA-Z]+','', fname).lower())
        sec['_pdf_path'] = pdf_path
        doc = fitz.open(pdf_path)
        pg = doc[sec['page_number'] - 1]
        rects = pg.search_for(sec['section_title'])
        sec['y_start'] = rects[0].y1 if rects else 0.0
        doc.close()

    # 2) group & sort per-document by (page, y_start)
    from collections import defaultdict
    doc_groups = defaultdict(list)
    for sec in section_list:
        doc_groups[sec['document']].append(sec)
    for lst in doc_groups.values():
        lst.sort(key=lambda s: (s['page_number'], s['y_start']))

    # 3) extract bodies
    results = []
    for sec in section_list:
        fname      = sec['document']
        title      = sec['section_title']
        page_n     = sec['page_number']
        y0         = sec['y_start']
        pdf_path   = sec['_pdf_path']
        group      = doc_groups[fname]
        idx        = group.index(sec)
        next_sec   = group[idx+1] if idx+1 < len(group) else None

        # determine same-page clip
        y1 = None
        if next_sec and next_sec['page_number']==page_n:
            y1 = next_sec['y_start']

        doc = fitz.open(pdf_path)
        body_lines = []

        # current page
        pg = doc[page_n-1]
        for block in pg.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                y = line['bbox'][1]
                if y < y0: continue
                if y1 is not None and y>=y1: continue
                text = ' '.join(span['text'] for span in line['spans']).strip()
                if text: body_lines.append(text)

        # pages in between
        if next_sec and next_sec['page_number']>page_n:
            for pno in range(page_n, next_sec['page_number']-1):
                pg2 = doc[pno]
                for block in pg2.get_text('dict')['blocks']:
                    for line in block.get('lines', []):
                        t = ' '.join(span['text'] for span in line['spans']).strip()
                        if t: body_lines.append(t)
            # clip next page up to its y_start
            pgn    = doc[next_sec['page_number']-1]
            y_end  = next_sec['y_start']
            for block in pgn.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    y = line['bbox'][1]
                    if y>=y_end: continue
                    t = ' '.join(span['text'] for span in line['spans']).strip()
                    if t: body_lines.append(t)

        doc.close()
        # join with spaces
        refined = ' '.join(body_lines)
        results.append({
            "document":      fname,
            "refined_text":  refined,
            "page_number":   page_n
        })

    return results
