**Task 1B: Heading Relevance Extraction**
=========================================

This project processes PDF heading outputs from Task 1A and selects those relevant to a given persona and job-to-be-done (from challenge1b\_input.json). It uses a lightweight embedding-based classifier (Sentence-Transformers all-MiniLM-L6-v2) to score heading relevance.

**Folder Structure**
--------------------

<img width="692" height="506" alt="image" src="https://github.com/user-attachments/assets/588f7835-82ae-4b31-b9d8-26ac27ebde0a" />

<img width="571" height="97" alt="image" src="https://github.com/user-attachments/assets/e7dc4306-e658-47a5-8b8d-39f083b5e6b6" />



**Prerequisites**
-----------------

*   Python 3.9+ (or Docker)
    
*   [pip](https://pip.pypa.io/en/stable/)
    
*   (Optional) [Docker](https://www.docker.com/) for containerized runs
    

**Installation (Local)**
------------------------

1.  Clone this repo:Bashgit clone cd project\_root
    
2.  Create & activate a venv (recommended):Bashpython3.9 -m venv venvsource venv/bin/activate
    
3.  Install dependencies:Bashpip install --no-cache-dir -r requirements.txt
    
4.  Ensure 1A/outputs/ contains your Task 1A JSONs and input/challenge1b\_input.json is present.
    

**Usage (Local)**
-----------------

To run the main Task 1B script locally, use the following command:

Bash

python -u src/main.py --input input\\pdfs --task1a 1A\\outputs --input-spec input\\challenge1b\_input.json --output output1b.json

*   \--threshold: cosine-similarity cutoff (default: 0.6).
    

**Usage (Docker)**
------------------

### **Task 1A Container**

1.  **Build the Task 1A image from the root directory:**Bashdocker build -t task1a:latest -f .\\1A\\docker\\Dockerfile .\\1A\\
    
2.  **Run the Task 1A container to process the PDFs:**Bashdocker run --rm -v "$(pwd)/input/pdfs:/app/input" -v "$(pwd)/1A/outputs:/app/output" task1a:latest
    

### **Task 1B Container**

1.  **Build the Task 1B image:**Bashdocker build -t task1b:latest .
    
2.  **Run the Task 1B container (mount volumes for PDFs and outputs):**Bashdocker run --rm \\ -v "$(pwd)/input:/app/input" \\ -v "$(pwd)/1A/outputs:/app/1A/outputs" \\ -v "$(pwd):/app" \\ task1b:latest \\ --input /app/input/pdfs \\ --task1a /app/1A/outputs \\ --input-spec /app/input/challenge1b\_input.json \\ --output /app/output1b.json
    

**Configuration**
-----------------

*   **Model**: all-MiniLM-L6-v2 (≈82 MB, fast inference)
    
*   **Threshold**: adjustable in config.py or via --threshold CLI flag.
    

**Next Steps**
--------------

*   Review & customize similarity threshold in config.py.
    
*   Integrate more sophisticated ranking or filtering logic in relevance.py.
    
*   Add unit tests for utils.py and similarity scoring.
