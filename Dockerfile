# Dockerfile for Task 1B
FROM python:3.9-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download model to allow offline inference
RUN python - <<EOF
from sentence_transformers import SentenceTransformer
SentenceTransformer('all-MiniLM-L6-v2')
EOF

# Copy project code and Task1A outputs
COPY src/ ./src/
COPY 1A/outputs/ ./1A/outputs/

# (Optional) copy input schema
COPY input/challenge1b_input.json ./input/challenge1b_input.json

# Default command: adjust volume mounts when running
CMD ["python", "-u", "src/main.py", "--input", "input", "--task1a", "1A/outputs", "--output", "output1b.json"]
