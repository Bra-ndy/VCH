#!/usr/bin/env bash
set -o errexit

echo "=== Installing dependencies ==="
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "=== Checking Flask installation ==="
python -c "import flask; print('Flask version:', flask.__version__)"

echo "=== Checking Gunicorn installation ==="
python -c "import gunicorn; print('Gunicorn version:', gunicorn.__version__)"

echo "=== Running database migrations ==="
python -m flask db upgrade || echo "Migration skipped"

echo "=== Build completed successfully ==="