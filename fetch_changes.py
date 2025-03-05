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

def process_listing_page(url, convert_to_md, output_file, processed_links):
    """Process a listing page: extract record links, fetch each record's content, and write to file.
    Returns the URL of the next listing page if available, otherwise None."""
    print(f"Processing listing page: {url}")
    page_content = fetch_page(url)
    if not page_content:
        return None

    soup = BeautifulSoup(page_content, 'html.parser')

    # Find change record links using the provided CSS selector.
    records = soup.select('.view-change-records .views-table td.views-field-title a')
    for record in records:
        href = record.get('href')
        # Convert relative URLs to absolute.
        full_url = requests.compat.urljoin(url, href)
        if full_url in processed_links:
            continue
        processed_links.add(full_url)
        print(f"  Fetching record: {full_url}")
        record_content = fetch_page(full_url)
        if record_content:
            record_soup = BeautifulSoup(record_content, 'html.parser')
            content_div = record_soup.find(id='content')
            if content_div:
                content_html = str(content_div)
                if convert_to_md and html2text:
                    md_converter = html2text.HTML2Text()
                    md_converter.ignore_links = False
                    content_to_write = md_converter.handle(content_html)
                else:
                    content_to_write = content_html
                # Append the fetched content into the output file.
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n--- Record: {full_url} ---\n\n")
                    f.write(content_to_write)
                    f.write("\n\n============================\n")
            else:
                print(f"    Could not find #content in {full_url}")
        else:
            print(f"    Failed to fetch {full_url}")

    # Look for the "next" page link using the pager selector.
    next_page_link = soup.select_one('.pager-next a')
    if next_page_link:
        next_href = next_page_link.get('href')
        next_url = requests.compat.urljoin(url, next_href)
        return next_url
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Fetch Drupal 11 change records and compile them into a single text file."
    )
    parser.add_argument(
        '--output', default='changes-11.txt', 
        help="Output file name (default: changes-11.txt)"
    )
    parser.add_argument(
        '--markdown', action='store_true', 
        help="Convert fetched HTML content to Markdown (requires html2text)"
    )
    args = parser.parse_args()

    # Starting listing URLs for different Drupal 11 branches.
    listing_urls = [
        "https://www.drupal.org/list-changes/drupal/published?keywords_description=&to_branch=11.0.x&version=&created_op=%3E%3D&created%5Bvalue%5D=&created%5Bmin%5D=&created%5Bmax%5D=",
        "https://www.drupal.org/list-changes/drupal/published?keywords_description=&to_branch=11.1.x&version=&created_op=%3E%3D&created%5Bvalue%5D=&created%5Bmin%5D=&created%5Bmax%5D=",
        "https://www.drupal.org/list-changes/drupal/published?keywords_description=&to_branch=11.2.x&version=&created_op=%3E%3D&created%5Bvalue%5D=&created%5Bmin%5D=&created%5Bmax%5D="
    ]

    output_file = args.output
    convert_to_md = args.markdown

    if convert_to_md and not html2text:
        print("Markdown conversion requested but html2text is not installed. Install it via pip (pip install html2text) or disable the markdown flag.")
        return

    # Clear the output file if it exists.
    open(output_file, 'w', encoding='utf-8').close()
    processed_links = set()

    # Process each starting listing URL, following pagination if present.
    for listing_url in listing_urls:
        next_page = listing_url
        while next_page:
            next_page = process_listing_page(next_page, convert_to_md, output_file, processed_links)
            # Be polite to the server.
            time.sleep(1)

if __name__ == "__main__":
    main()
