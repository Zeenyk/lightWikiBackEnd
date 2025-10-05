import json
import os
import re
import glob
from datetime import datetime

def parse_markdown_file(file_path):
    """
    Parse a Markdown file and extract the required parameters for JSON output.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML frontmatter
    frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return None
    
    frontmatter = frontmatter_match.group(1)
    
    # Extract title
    title_match = re.search(r'title:\s*"([^"]+)"', frontmatter)
    title = title_match.group(1) if title_match else "Unknown Title"
    
    # Extract authors and tags from authors field
    authors_match = re.search(r'authors:\s*(.+)', frontmatter)
    authors_tags_text = authors_match.group(1) if authors_match else ""
    
    # Parse authors and tags
    authors = []
    tags = []
    
    # Split by commas and process each item
    items = [item.strip() for item in authors_tags_text.split(',')]
    
    for item in items:
        # Check if it's an author (starts with one or two capital letters followed by a space and a word)
        if re.match(r'^[A-Z]{1,2}[a-z]*\s+[A-Z][a-z]+', item):
            authors.append(item)
        else:
            # It's a tag (one or more words)
            tags.append(item)
    
    # Extract date from scraped_date
    date_match = re.search(r'scraped_date:\s*(\d{4}-\d{2}-\d{2})', frontmatter)
    date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
    
    # Extract URL
    url_match = re.search(r'url:\s*(https?://[^\s]+)', frontmatter)
    url = url_match.group(1) if url_match else ""
    
    # Extract page content (everything after the second --- separator)
    content_parts = content.split('---')
    if len(content_parts) >= 3:
        # Get everything after the second ---
        pagecontent = '---'.join(content_parts[2:]).strip()
        
        # Remove the header block (everything before the actual content starts)
        # Look for the first occurrence of a major section like Abstract or Introduction
        content_start_patterns = [
            r'##\s*Abstract',
            r'##\s*Introduction', 
            r'##\s*[A-Z][a-z]+',
            r'#\s*[A-Z][a-z]+'
        ]
        
        for pattern in content_start_patterns:
            match = re.search(pattern, pagecontent, re.IGNORECASE)
            if match:
                pagecontent = pagecontent[match.start():]
                break
    else:
        pagecontent = ""
    
    # Create the JSON structure
    result = {
        "title": title,
        "date": date,
        "authors": authors,
        "tags": tags,
        "pagecontent": pagecontent,
        "page": {
            "url": url
        }
    }
    
    return result

def generate_json_from_directory(input_dir, output_file):
    """
    Generate JSON from all Markdown files in a directory.
    """
    # Find all .md files in the directory (excluding template files)
    md_files = glob.glob(os.path.join(input_dir, "*.md"))
    md_files = [f for f in md_files if not f.endswith('0template.md')]
    
    results = []
    
    for md_file in md_files:
        print(f"Processing: {os.path.basename(md_file)}")
        parsed_data = parse_markdown_file(md_file)
        if parsed_data:
            results.append(parsed_data)
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Generated JSON with {len(results)} entries to {output_file}")
    return results

def main():
    """
    Main function to process scraped content and generate JSON.
    """
    input_dir = 'scraped_content'
    output_file = 'papers_data.json'
    
    if not os.path.exists(input_dir):
        print(f"Error: Directory '{input_dir}' does not exist.")
        return
    
    generate_json_from_directory(input_dir, output_file)

if __name__ == '__main__':
    main()
