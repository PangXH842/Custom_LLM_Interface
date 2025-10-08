# proj/backend/scripts/convert_clauses_to_json.py

import json
import os
import re

# --- CONFIGURATION ---
INPUT_FILENAME = "1.txt"
OUTPUT_FILENAME = "1.json"

# Construct the full paths
scripts_dir = os.path.dirname(__file__)
data_dir = os.path.join(scripts_dir, '..', 'data')
INPUT_TEXT_FILE = os.path.join(data_dir, INPUT_FILENAME)
OUTPUT_JSON_FILE = os.path.join(data_dir, OUTPUT_FILENAME)

def clean_text(text): 
    # strip "1) text" 
    return re.sub(r'\s+', ' ', text).strip()

def process_text_to_json():
    """
    Reads a text file with parent (e.g., '14)') and child (e.g., 'a)') clauses
    and groups them into single JSON objects.
    """
    try:
        with open(INPUT_TEXT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"ERROR: Input file not found at '{INPUT_TEXT_FILE}'")
        return

    knowledge_base = []
    current_clause_number = None
    current_clause_content = []

    # Regex to detect main clauses (e.g., "1)", "14)") and sub-clauses (e.g., "a)", "b)")
    main_clause_pattern = re.compile(r'^\s*(\d{1,2})\)')
    sub_clause_pattern = re.compile(r'^\s*([a-z])\)')
    
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        main_match = main_clause_pattern.match(stripped_line)
        
        if main_match:
            # --- Found a NEW main clause ---

            # First, save the PREVIOUS clause we were building (if it exists)
            if current_clause_number and current_clause_content:
                combined_content = " ".join(current_clause_content)
                knowledge_base.append({
                    "source": f"Sample Tenancy Agreement - Clause {current_clause_number}",
                    "content": clean_text(combined_content)
                })

            # Now, start the NEW clause
            current_clause_number = main_match.group(1)
            current_clause_content = [stripped_line]
        
        elif current_clause_number:
            # --- This line is part of the current clause (either a sub-clause or continuation) ---
            current_clause_content.append(stripped_line)

    # After the loop, save the very last clause that was being built
    if current_clause_number and current_clause_content:
        combined_content = " ".join(current_clause_content)
        knowledge_base.append({
            "source": f"Sample Tenancy Agreement - Clause {current_clause_number}",
            "content": clean_text(combined_content)
        })

    return knowledge_base

def main():
    """Main function to run the conversion."""
    print(f"Reading and processing clauses from: {INPUT_TEXT_FILE}")
    
    json_output = process_text_to_json()

    if json_output:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2)
            
        print(f"\nSuccess! Conversion complete. {len(json_output)} comprehensive clauses have been created.")
        print(f"JSON knowledge base saved to: {OUTPUT_JSON_FILE}")
    else:
        print("\nWarning: No clauses were processed. Check the input file format.")


if __name__ == '__main__':
    main()