#!/bin/bash
set -e

echo "=== VCH Build Starting ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Create and activate virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies with verbose output
echo "Installing dependencies from requirements.txt..."
python -m pip install -r requirements.txt --verbose

# Verify critical packages
echo "Verifying installations..."
python -c "import flask; print(f'✅ Flask {flask.__version__} installed')"
python -c "import gunicorn; print(f'✅ Gunicorn {gunicorn.__version__} installed')"
python -c "import flask_sqlalchemy; print(f'✅ Flask-SQLAlchemy installed')"

# Run migrations (if migrations folder exists)
echo "Running database migrations..."
if [ -d "migrations" ]; then
    python -m flask db upgrade
else
    echo "⚠️ No migrations folder found, skipping..."
fi

echo "=== Build completed successfully ==="