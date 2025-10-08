# proj/backend/scripts/convert_rules_to_json.py

import json
import os
import re

# --- CONFIGURATION ---
INPUT_FILENAME = "rental_rules.txt"
OUTPUT_FILENAME = "rental_rules.json"

# Construct the full paths
scripts_dir = os.path.dirname(__file__)
data_dir = os.path.join(scripts_dir, '..', 'data')
INPUT_TEXT_FILE = os.path.join(data_dir, INPUT_FILENAME)
OUTPUT_JSON_FILE = os.path.join(data_dir, OUTPUT_FILENAME)

def clean_text(text):
    # strip "1. text"
    return re.sub(r'\s+', ' ', text).strip()

def process_rules_file():
    """
    Reads the multi-source rules file, splits it into sections,
    and then chunks each numbered point into a JSON object.
    """
    try:
        with open(INPUT_TEXT_FILE, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except FileNotFoundError:
        print(f"ERROR: Input file not found at '{INPUT_TEXT_FILE}'")
        return None

    knowledge_base = []
    
    # Regex to split the text by the main headers (e.g., "from HDB website:")
    # It captures the source name (HDB, URA, Property Guru, SSO).
    # The `(?i)` makes it case-insensitive. `[\w\s]+` captures multi-word names.
    sections = re.split(r'(?i)Regulations for Renting a Flat/ Bedroom from ([\w\s]+):', full_text)

    # We iterate through the list in steps of 2: the source name and its content.
    # The first item in `sections` is usually empty text before the first header.
    for i in range(1, len(sections), 2):
        source_name = sections[i].replace('website', '').strip()
        content = sections[i+1]
        
        # Now, split the content of this section by its numbered points
        points = re.split(r'\n\s*(\d{1,2})\.\s*', content)
        
        # Again, the first item is text before the first number, which we can often ignore
        # unless it's an introduction. We'll add it as a general point.
        if points[0].strip():
            knowledge_base.append({
                "source": f"{source_name} Regulations - General Intro",
                "content": clean_text(points[0])
            })
            
        for j in range(1, len(points), 2):
            point_number = points[j]
            point_text = points[j+1]
            
            knowledge_base.append({
                "source": f"{source_name} Regulations - Point {point_number}",
                "content": clean_text(point_text)
            })

    return knowledge_base

def main():
    """Main function to run the conversion."""
    print(f"Reading and processing rules from: {INPUT_TEXT_FILE}")
    
    json_output = process_rules_file()

    if json_output:
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2)
            
        print(f"\nSuccess! Conversion complete.")
        print(f"{len(json_output)} rule entries have been created.")
        print(f"JSON knowledge base saved to: {OUTPUT_JSON_FILE}")
    else:
        print("\nWarning: No rules were processed. Check the input file format and headers.")

if __name__ == '__main__':
    main()