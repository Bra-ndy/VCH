#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
python -m pip install -r requirements.txt

# Run migrations (skip if no migrations folder)
python -m flask db upgrade || echo "Migration skipped"

echo "Build completed successfully."