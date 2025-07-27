# src/relevance.py

"""
Module for embedding-based relevance filtering of Task 1A headings
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from config import MODEL_NAME, DEFAULT_THRESHOLD

# Load model once at import
_model = SentenceTransformer(MODEL_NAME)


def _embed_texts(texts):
    """
    Encode a list of texts into embeddings.
    """
    return _model.encode(texts, convert_to_tensor=False)


def _cosine_sim(a, b):
    """
    Compute cosine similarity between two 1D numpy arrays.
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def filter_headings(input_spec, task1a_outputs, threshold=DEFAULT_THRESHOLD):
    """
    Given the input spec dict (with keys 'persona' and 'job_to_be_done')
    and a dict of Task 1A outputs (mapping doc_name -> output_json),
    return a dict mapping each doc_name to a list of relevant headings.

    Each heading entry preserves its original fields plus an added 'score'.
    """
    # Prepare the spec embedding
    persona = input_spec.get('persona', '')
    job = input_spec.get('job_to_be_done', '')
    spec_text = persona + ' ' + job
    spec_emb = _embed_texts([spec_text])[0]

    results = {}
    for doc_name, data in task1a_outputs.items():
        # Expecting an 'outline' key with a list of heading objects
        headings = data.get('outline', [])
        texts = [h.get('text', '') for h in headings]
        if not texts:
            results[doc_name] = []
            continue

        embs = _embed_texts(texts)
        relevant = []

        for heading_obj, emb in zip(headings, embs):
            score = _cosine_sim(spec_emb, emb)
            if score >= threshold:
                entry = heading_obj.copy()
                entry['score'] = score
                relevant.append(entry)

        # Sort by descending score
        relevant.sort(key=lambda x: x['score'], reverse=True)
        results[doc_name] = relevant

    return results
