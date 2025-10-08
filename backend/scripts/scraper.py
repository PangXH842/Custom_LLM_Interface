# proj/backend/scripts/downloader_and_extractor.py

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse, quote

# --- CONFIGURATION ---

# List of URLs you want to process.
URLS_TO_PROCESS = [
    'https://www.cea.gov.sg/consumers/property-rental-process/renting-a-residential-property-in-singapore',
    'https://www.ura.gov.sg/dc/resident/A-Z-of-Residential-Dev-and-Other-Related-Information/renting-a-private-property'
]

# Politeness configuration for downloading
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
REQUEST_DELAY_SECONDS = 2

# --- FILE PATHS ---
# We will create a new folder to store the raw HTML files.
scripts_dir = os.path.dirname(__file__)
data_dir = os.path.join(scripts_dir, '..', 'data')
raw_html_dir = os.path.join(data_dir, 'raw_html_pages')
output_json_path = os.path.join(data_dir, 'scraped_knowledge_base.json')

# --- STAGE 1: DOWNLOADING ---

def sanitize_filename(url):
    """Creates a safe filename from a URL."""
    # Use the path part of the URL, remove scheme and netloc
    path = urlparse(url).path
    # Replace slashes and invalid chars, then trim length
    safe_name = quote(path, safe='').replace('%', '_').strip('_')
    return safe_name[:100] + ".html"

def download_pages():
    """Downloads all URLs from the list and saves them as local HTML files."""
    print("--- STAGE 1: DOWNLOADING WEBPAGES ---")
    os.makedirs(raw_html_dir, exist_ok=True)
    
    for url in URLS_TO_PROCESS:
        filename = sanitize_filename(url)
        filepath = os.path.join(raw_html_dir, filename)

        if os.path.exists(filepath):
            print(f"Skipping download, file already exists: {filename}")
            continue

        try:
            print(f"Downloading: {url}")
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"  -> Saved to {filename}")

        except requests.RequestException as e:
            print(f"  -> FAILED to download {url}: {e}")
        
        print(f"Waiting for {REQUEST_DELAY_SECONDS} seconds...")
        time.sleep(REQUEST_DELAY_SECONDS)

# --- STAGE 2: EXTRACTION ---

def parse_cea_page(soup):
    """Resilient parser for cea.gov.sg."""
    content_div = soup.find('div', id=lambda x: x and x.startswith('contentplaceholder_')) or \
                  soup.find('div', class_='sf-content-block')
    return content_div.get_text(separator='\n', strip=True) if content_div else None

def parse_ura_page(soup):
    """Resilient parser for ura.gov.sg."""
    content_div = soup.find('div', id='content') or \
                  soup.find('div', class_='ura-rte-styles')
    return content_div.get_text(separator='\n', strip=True) if content_div else None

SITE_PARSERS = {
    'www.cea.gov.sg': parse_cea_page,
    'www.ura.gov.sg': parse_ura_page,
}

def extract_text_from_files():
    """Reads local HTML files, parses them, and returns a list of extracted data."""
    print("\n--- STAGE 2: EXTRACTING TEXT FROM LOCAL FILES ---")
    knowledge_data = []

    for url in URLS_TO_PROCESS:
        filename = sanitize_filename(url)
        filepath = os.path.join(raw_html_dir, filename)

        if not os.path.exists(filepath):
            print(f"Skipping extraction, file not found: {filename}")
            continue
            
        print(f"Extracting from: {filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        
        domain = urlparse(url).netloc
        parser = SITE_PARSERS.get(domain)

        if not parser:
            print(f"  -> Warning: No parser for this domain ({domain}). Skipping.")
            continue

        text = parser(soup)
        if text:
            knowledge_data.append({
                'source': url, # Use the original URL as the source
                'content': text
            })
            print(f"  -> Success: Content extracted.")
        else:
            print(f"  -> Warning: Parser failed to find content.")
            
    return knowledge_data

# --- MAIN ORCHESTRATOR ---

def main():
    """Runs the full download and extraction pipeline."""
    # Stage 1: Get the raw HTML
    download_pages()
    
    # Stage 2: Process the downloaded files
    extracted_data = extract_text_from_files()
    
    # Save the final result
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nPipeline complete! Knowledge base saved to {output_json_path}")
    if not extracted_data:
        print("\nWarning: The final knowledge base is empty. Check for download or parsing errors above.")

if __name__ == '__main__':
    main()