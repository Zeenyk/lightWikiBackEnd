#!/bin/bash

# Setup script for scraper virtual environment
echo "Setting up Python virtual environment for scraper..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "source venv/bin/activate"
echo ""
echo "To run the scraper:"
echo "python scraper.py -n 10"
