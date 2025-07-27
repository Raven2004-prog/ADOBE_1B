# Dockerfile for Task 1B (offline-ready)

FROM python:3.9-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tell HF libraries to stay offline once assets are present
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

# Pre-download bi-encoder & cross-encoder models into the cache
RUN python - <<'EOF'
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 1) SBERT bi-encoder
SentenceTransformer("all-MiniLM-L6-v2")

# 2) Cross-encoder reranker
AutoTokenizer.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
AutoModelForSequenceClassification.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
EOF

# Copy project code and Task 1A outputs
COPY src/ ./src/
COPY 1A/outputs/ ./1A/outputs/
COPY input/challenge1b_input.json ./input/challenge1b_input.json

# Default command
CMD ["python", "-u", "src/main.py", "--input", "input/pdfs", "--task1a", "1A/outputs", "--output", "output1b.json"]
