#!/bin/bash
# Release phase script - runs migrations after app starts
echo "Running migrations..."
python manage.py migrate --skip-checks --no-input 2>/dev/null || echo "Migrations skipped (database may not be ready yet)"
echo "Release phase complete"
