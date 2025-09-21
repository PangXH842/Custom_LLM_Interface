# proj/backend/scripts/scraper.py

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse

# --- Respectful Scraping Configuration ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}
REQUEST_DELAY_SECONDS = 2

# --- Site-Specific Parsers ---
# Each function knows how to find the main content for a specific website.

def parse_cea_page(soup):
    """Parser for cea.gov.sg"""
    content_div = soup.find('div', class_='sf-content-block')
    return content_div.get_text(separator='\n', strip=True) if content_div else None

def parse_ura_page(soup):
    """Parser for ura.gov.sg"""
    content_div = soup.find('div', class_='ura-rte-styles')
    return content_div.get_text(separator='\n', strip=True) if content_div else None

def parse_propertyguru_page(soup):
    """Parser for propertyguru.com.sg"""
    content_div = soup.find('div', class_='property-guides-content')
    return content_div.get_text(separator='\n', strip=True) if content_div else None


# This dictionary maps a domain name to its specific parsing function.
SITE_PARSERS = {
    'www.cea.gov.sg': parse_cea_page,
    'www.ura.gov.sg': parse_ura_page,
    'www.propertyguru.com.sg': parse_propertyguru_page,
}

def get_parser_for_url(url):
    """Looks up the correct parser function based on the URL's domain."""
    domain = urlparse(url).netloc
    return SITE_PARSERS.get(domain)


def scrape_page(url):
    """Scrapes a single content page using the correct site-specific parser."""
    parser = get_parser_for_url(url)
    if not parser:
        print(f"  -> Warning: No parser available for this domain. Skipping.")
        return None

    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Fix for potential character encoding issues
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = parser(soup) # Use the specific parser for this site
        
        if text:
            print(f"  -> Success: Content extracted.")
            return text
        else:
            print(f"  -> Warning: Parser failed to find content.")
            return None
            
    except requests.RequestException as e:
        print(f"  -> Error fetching {url}: {e}")
        return None

def run_scraper():
    """Main function to run the scraper and save the data."""
    print("Starting multi-source scraper...")
    
    # Updated list, removing the problematic 99.co
    urls_to_scrape = [
        # --- CEA ---
        'https://www.cea.gov.sg/consumers/engaging-a-property-agent/',
        # --- URA ---
        'https://www.ura.gov.sg/Corporate/Property/Residential/Renting-Property',
    ]

    scraped_data = []
    for url in urls_to_scrape:
        content = scrape_page(url)
        if content:
            scraped_data.append({'source': url, 'content': content})
        
        print(f"Waiting for {REQUEST_DELAY_SECONDS} seconds...")
        time.sleep(REQUEST_DELAY_SECONDS)

    # We'll use the new filename from your error message
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    output_path = os.path.join(data_dir, 'combined_knowledge_base.json')
    os.makedirs(data_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)

    print(f"\nScraping complete! Data saved to {output_path}")

if __name__ == '__main__':
    run_scraper()