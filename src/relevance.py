# src/relevance.py

"""
Two-stage relevance filtering: fast bi-encoder recall + cross-encoder rerank.
"""

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from config import MODEL_NAME, TOP_K_RERANK

# Stage 1: bi-encoder
_bi_encoder = SentenceTransformer(MODEL_NAME)

# Stage 2: cross-encoder for reranking (MS-MARCO fine-tuned)
_rerank_tokenizer = AutoTokenizer.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
_rerank_model     = AutoModelForSequenceClassification.from_pretrained(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def filter_headings(input_spec, task1a_outputs, threshold=None):
    """
    Perform two-stage retrieval:
      1) Bi-encoder to score all headings and select top-K
      2) Cross-encoder to rerank those top-K for final precision

    Returns:
      dict mapping doc_name -> list of heading dicts with 'score' (cross-encoder logits)
    """
    # Prepare query text
    persona = input_spec.get('persona', '')
    job     = input_spec.get('job_to_be_done', '')
    spec_text = persona + ' ' + job

    # Flatten all headings across documents
    records = []  # each: { 'doc':doc_name, 'text':heading_text, 'meta':orig_heading_obj }
    for doc_name, data in task1a_outputs.items():
        for h in data.get('outline', []):
            records.append({
                'doc': doc_name,
                'text': h.get('text', ''),
                'meta': h
            })
    if not records:
        return {}

    # Stage 1: bi-encoder embeddings + cosine
    spec_emb = _bi_encoder.encode([spec_text], convert_to_tensor=False)[0]
    texts    = [r['text'] for r in records]
    emb_list = _bi_encoder.encode(texts, convert_to_tensor=False)
    bi_scores = [ _cosine_sim(spec_emb, emb) for emb in emb_list ]

    # Select top-K indices
    topk_idx = sorted(range(len(bi_scores)), key=lambda i: bi_scores[i], reverse=True)[:TOP_K_RERANK]

    # Stage 2: cross-encoder rerank
    spec_inputs = [spec_text] * len(topk_idx)
    head_texts  = [texts[i] for i in topk_idx]
    inputs = _rerank_tokenizer(
        spec_inputs,
        head_texts,
        padding=True,
        truncation=True,
        return_tensors='pt'
    )
    with torch.no_grad():
        logits = _rerank_model(**inputs).logits.squeeze(-1).tolist()

    # Sort top-K by cross-encoder score
    reranked = sorted(zip(topk_idx, logits), key=lambda x: x[1], reverse=True)

    # Collect into per-document mapping
    results = {}
    for idx, score in reranked:
        rec = records[idx]
        doc = rec['doc']
        entry = rec['meta'].copy()
        entry['score'] = score
        results.setdefault(doc, []).append(entry)

    return results
