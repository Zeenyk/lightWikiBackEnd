# Web Scraper for PubMed Articles

A Python-based web scraper that extracts content from PubMed articles and converts them to Markdown format.

## Features

- Scrapes PubMed article content from CSV URLs
- Converts HTML to clean Markdown format
- Replaces author links with search placeholders
- Handles redirects and timeouts
- Generates safe, filesystem-compatible filenames

## Setup

### Prerequisites
- Python 3.8 or higher
- `python3-venv` package (for virtual environment)

### Installation

1. **Navigate to the scraper directory:**
   ```bash
   cd lightWikiBackEnd/scraper
   ```

2. **Run the setup script:**
   ```bash
   ./setup_venv.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

### Manual Setup (Alternative)

If the setup script doesn't work, you can manually create the virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Activate virtual environment first
source venv/bin/activate

# Scrape 10 articles (default)
python scraper.py

# Scrape specific number of articles
python scraper.py -n 5
```

### Input Data
The scraper reads URLs from `csv/SB_publication_PMC.csv` which should contain a 'Link' column with PubMed URLs.

### Output
Scraped content is saved as Markdown files in the `scraped_content/` directory.

## Dependencies

- `beautifulsoup4` - HTML parsing
- `requests` - HTTP requests
- `html2text` - HTML to Markdown conversion
- Supporting packages for HTTP and encoding

## Troubleshooting

### Externally Managed Environment Error
If you encounter the "externally-managed-environment" error, use the virtual environment setup as described above.

### Missing Dependencies
Ensure all dependencies are installed in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### File Permissions
If the setup script is not executable:
```bash
chmod +x setup_venv.sh
```

## File Structure
```
scraper/
├── scraper.py          # Main scraper script
├── requirements.txt    # Python dependencies
├── setup_venv.sh      # Virtual environment setup
├── csv/               # Input CSV files
│   └── SB_publication_PMC.csv
└── scraped_content/   # Output directory for Markdown files
