#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
python -m flask db upgrade || echo "Migration skipped"