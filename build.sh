#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run migrations
python -m flask db upgrade || echo "Migration skipped"