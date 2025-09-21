# proj/backend/scripts/scraper_local.py

import os
import json
from bs4 import BeautifulSoup

def parse_local_cea_page(soup):
    """
    This is a parser specifically designed for the locally saved CEA HTML file.
    It looks for the <main> HTML tag which contains all the article content.
    """
    # The main content of the article is inside the <main> tag with this ID.
    main_content = soup.find('main', id='main-content')
    if main_content:
        # We can be even more specific and find the column div inside main
        article_column = main_content.find('div', class_='lg:col-span-9')
        if article_column:
            return article_column.get_text(separator='\n', strip=True)
    return None # Return None if we couldn't find the content

def process_local_files():
    """
    Reads local HTML files from the data directory, parses them,
    and saves the content to a JSON knowledge base.
    """
    print("Starting local HTML file processor...")

    # --- Define Paths ---
    # The directory where this script lives
    scripts_dir = os.path.dirname(__file__)
    # The data directory, where both input HTML and output JSON will be
    data_dir = os.path.join(scripts_dir, '..', 'data')
    
    # List of local HTML files you want to process
    html_files_to_process = [
        "What to take note of when engaging a property agent _ Council for Estate Agencies.html"
        # You can add more downloaded HTML files to this list later!
    ]

    scraped_data = []
    for file_name in html_files_to_process:
        file_path = os.path.join(data_dir, file_name)
        print(f"Processing: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')
            content = parse_local_cea_page(soup)

            if content:
                scraped_data.append({
                    'source': file_name,  # The source is now the local file name
                    'content': content
                })
                print(f"  -> Success: Content extracted.")
            else:
                print(f"  -> Warning: Parser failed to find content in this file.")

        except FileNotFoundError:
            print(f"  -> Error: File not found! Make sure '{file_name}' is in the 'backend/data' folder.")
        except Exception as e:
            print(f"  -> An unexpected error occurred: {e}")

    # --- Save the Output ---
    output_path = os.path.join(data_dir, 'local_knowledge_base.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)

    print(f"\nProcessing complete! Data saved to {output_path}")

if __name__ == '__main__':
    process_local_files()