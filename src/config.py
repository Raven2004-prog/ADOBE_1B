"""
Configuration constants for Task 1B
"""

# Sentence-Transformers model identifier
MODEL_NAME = "all-MiniLM-L6-v2"

# Cosine similarity threshold for heading relevance (unused when using reranking)
DEFAULT_THRESHOLD = 0.4

# Number of top candidates from bi-encoder to rerank via cross-encoder
TOP_K_RERANK = 50

# Default file paths (relative to project root)
DEFAULT_INPUT_PDF_DIR = "input/pdfs"
DEFAULT_TASK1A_OUTPUT_DIR = "1A/outputs"
DEFAULT_INPUT_SPEC_FILE = "input/challenge1b_input.json"
DEFAULT_OUTPUT_FILE = "output1b.json"
