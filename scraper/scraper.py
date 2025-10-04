
import csv
import requests
from bs4 import BeautifulSoup
import os
import argparse

def scrape_url(url, output_dir):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the main content of the article
        article_body = soup.find('div', id='mc') # Common ID for main content in PMC articles

        if article_body:
            text_content = article_body.get_text(separator='\n', strip=True)
            # Create a filename from the URL
            filename = url.split('/')[-2] + '.txt'
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"Scraped and saved content from {url} to {filepath}")
        else:
            print(f"Could not find main content for {url}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Scrape URLs from a CSV file.')
    parser.add_argument('-n', type=int, default=10, help='Number of URLs to scrape.')
    args = parser.parse_args()

    csv_file = 'csv/SB_publication_PMC.csv'
    output_dir = 'scraped_content'
    os.makedirs(output_dir, exist_ok=True)

    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= args.n:
                break
            url = row.get('Link')
            if url:
                scrape_url(url, output_dir)

if __name__ == '__main__':
    main()
