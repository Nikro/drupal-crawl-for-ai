#!/usr/bin/env python3
import argparse
import time
import requests
from bs4 import BeautifulSoup

# If you want to convert HTML to Markdown, install html2text and enable the flag.
try:
    import html2text
except ImportError:
    html2text = None

def fetch_page(url):
    """Fetch a page and return its text content, or None on error."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def process_api_links(base_url, convert_to_md, output_file, processed_links):
    """Process the API documentation page: extract links and fetch each page's content"""
    print(f"Processing API page: {base_url}")
    page_content = fetch_page(base_url)
    if not page_content:
        return None

    soup = BeautifulSoup(page_content, 'html.parser')
    
    # Find all API documentation links in the left content region
    api_links = soup.select('.column-content-region.left-content .panel-panel-inner a')
    
    for link in api_links:
        href = link.get('href')
        # Convert relative URLs to absolute
        full_url = requests.compat.urljoin(base_url, href)
        
        if full_url in processed_links:
            continue
            
        processed_links.add(full_url)
        print(f"  Fetching API doc: {full_url}")
        
        # Be polite to the server
        time.sleep(2)
        
        doc_content = fetch_page(full_url)
        if doc_content:
            doc_soup = BeautifulSoup(doc_content, 'html.parser')
            
            # Find the content in the specified selector
            content_div = doc_soup.select_one('.panel-panel-inner .pane-node-body .pane-content')
            if content_div:
                content_html = str(content_div)
                
                if convert_to_md and html2text:
                    md_converter = html2text.HTML2Text()
                    md_converter.ignore_links = False
                    content_to_write = md_converter.handle(content_html)
                else:
                    content_to_write = content_html
                    
                # Append the fetched content into the output file
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n--- API Document: {full_url} ---\n\n")
                    f.write(content_to_write)
                    f.write("\n\n============================\n")
            else:
                print(f"    Could not find content in {full_url}")
        else:
            print(f"    Failed to fetch {full_url}")

def main():
    parser = argparse.ArgumentParser(
        description="Fetch Drupal API documentation and compile it into a single text file."
    )
    parser.add_argument(
        '--output', default='drupal-api-docs.txt', 
        help="Output file name (default: drupal-api-docs.txt)"
    )
    parser.add_argument(
        '--markdown', action='store_true', 
        help="Convert fetched HTML content to Markdown (requires html2text)"
    )
    args = parser.parse_args()
    
    # API documentation base URL
    api_base_url = "https://www.drupal.org/docs/develop/drupal-apis"

    output_file = args.output
    convert_to_md = args.markdown

    if convert_to_md and not html2text:
        print("Markdown conversion requested but html2text is not installed. Install it via pip (pip install html2text) or disable the markdown flag.")
        return

    # Clear the output file if it exists
    open(output_file, 'w', encoding='utf-8').close()
    processed_links = set()

    # Process the API documentation page
    process_api_links(api_base_url, convert_to_md, output_file, processed_links)

if __name__ == "__main__":
    main()