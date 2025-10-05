
import csv
import requests
from bs4 import BeautifulSoup
import os
import argparse
import html2text
import re
import datetime
from urllib.parse import urlparse

def process_internal_references(markdown_content):
    """
    Convert internal page references (Figure X, Table X, Section names) to proper Markdown links.
    """
    # Process figure references
    markdown_content = re.sub(
        r'Figure (\d+)',
        r'[Figure \1](#figure-\1)',
        markdown_content
    )
    
    # Process table references  
    markdown_content = re.sub(
        r'Table (\d+)',
        r'[Table \1](#table-\1)',
        markdown_content
    )
    
    # Process section references (common section names)
    section_patterns = [
        (r'Introduction', '[Introduction](#introduction)'),
        (r'Materials and Methods', '[Materials and Methods](#materials-and-methods)'),
        (r'Results', '[Results](#results)'),
        (r'Discussion', '[Discussion](#discussion)'),
        (r'Conclusion', '[Conclusion](#conclusion)'),
        (r'References', '[References](#references)'),
        (r'Abstract', '[Abstract](#abstract)'),
        (r'Methods', '[Methods](#methods)'),
        (r'Background', '[Background](#background)'),
        (r'Acknowledgments', '[Acknowledgments](#acknowledgments)'),
        (r'Funding Statement', '[Funding Statement](#funding-statement)'),
    ]
    
    for pattern, replacement in section_patterns:
        markdown_content = re.sub(pattern, replacement, markdown_content)
    
    return markdown_content

def scrape_url(url, output_dir):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract paper title
        title = soup.find('h1') or soup.find('title')
        paper_title = title.get_text(strip=True) if title else "Unknown Title"
        
        # Find the main content of the article
        article_body = soup.find('article')  # More general selector
        
        # Extract author names
        authors = []
        
        if article_body:
            # Method 1: Look for author links in the article body first (most reliable)
            author_links = article_body.find_all('a', href=lambda href: href and "pubmed.ncbi.nlm.nih.gov" in href and "%22%5BAuthor%5D" in href)
            for link in author_links:
                author_name = link.get_text(strip=True)
                if author_name and author_name not in authors:
                    authors.append(author_name)
        
        # Method 2: Look for author elements with specific class patterns
        author_selectors = [
            'span[class*="author"]',
            'div[class*="author"]', 
            'span[class*="contrib"]',
            'div[class*="contrib"]',
            'span[class*="auth"]',
            'div[class*="auth"]',
            '.author-name',
            '.contrib-author',
            '.fm-author'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 2 and len(text) < 50:  # Reasonable author name length
                    # Clean up author names (remove numbers, special characters, etc.)
                    clean_name = re.sub(r'[0-9\*†‡§¶#]', '', text).strip()
                    # Check if it looks like a person's name (at least two words, starts with capital)
                    if (clean_name and 
                        len(clean_name.split()) >= 2 and 
                        clean_name[0].isupper() and
                        clean_name not in authors):
                        authors.append(clean_name)
        
        # Method 3: Look for author names in specific sections
        author_sections = soup.find_all(['div', 'section'], 
                                      class_=lambda x: x and any(keyword in str(x).lower() 
                                      for keyword in ['author', 'contrib', 'affiliation']))
        
        for section in author_sections:
            # Look for text that matches name patterns
            name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
            matches = name_pattern.findall(section.get_text())
            for match in matches:
                if len(match) > 4 and match not in authors:
                    authors.append(match)
        
        # Clean and deduplicate authors
        authors = list(dict.fromkeys(authors))[:15]  # Remove duplicates, limit to 15 authors
        
        if article_body:
            # Replace author links with placeholders
            for author_link in article_body.find_all('a', href=lambda href: href and "pubmed.ncbi.nlm.nih.gov" in href and "%22%5BAuthor%5D" in href):
                author_name = author_link.get_text(strip=True)
                author_link.replace_with(f'(:SearchAuthor:[{author_name}])')
            
            # Convert HTML to Markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            markdown_content = h.handle(str(article_body))
            
            # Process internal page references to create links
            markdown_content = process_internal_references(markdown_content)
            
            # Create standardized header block
            header_block = f"""---
title: "{paper_title}"
authors: {', '.join(authors) if authors else 'Unknown Authors'}
url: {url}
scraped_date: {datetime.datetime.now().strftime('%Y-%m-%d')}
---

# {paper_title}

**Authors:** {', '.join(authors) if authors else 'Unknown Authors'}  
**Source:** {url}  
**Scraped:** {datetime.datetime.now().strftime('%Y-%m-%d')}

---

"""
            
            # Create a safe filename from the URL
            parsed_url = urlparse(url)
            # Extract PMC ID or use last path component
            path_parts = [p for p in parsed_url.path.split('/') if p]
            if path_parts:
                filename_base = path_parts[-1] if path_parts[-1] else path_parts[-2] if len(path_parts) > 1 else 'unknown'
            else:
                filename_base = 'unknown'
            
            # Clean filename to be filesystem-safe
            filename_base = re.sub(r'[^\w\-_.]', '_', filename_base)
            filename = f"{filename_base}.md"
            filepath = os.path.join(output_dir, filename)
            
            # Write content to file with header
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(header_block + markdown_content)
            print(f"Scraped and saved content from {url} to {filepath}")
            print(f"  Title: {paper_title}")
            print(f"  Authors: {len(authors)} found")
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
