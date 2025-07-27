# src/utils.py

import os
import json
import glob

def load_input_spec(spec_path):
    """
    Load the challenge1b_input.json which contains persona and job-to-be-done.
    """
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_task1a_outputs(outputs_dir):
    """
    Read every JSON file in the Task 1A outputs directory.
    Returns a dict mapping each PDF’s basename (no extension) to its loaded JSON.
    """
    outputs = {}
    pattern = os.path.join(outputs_dir, '*.json')
    for filepath in glob.glob(pattern):
        key = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            outputs[key] = json.load(f)
    return outputs

def write_output1b(result_dict, output_path):
    """
    Write the final 1B output JSON. 
    `result_dict` should match the schema of output1b_json.
    """
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
