web: ENVIRONMENT=production python manage.py migrate --skip-checks 2>/dev/null || true; ENVIRONMENT=production gunicorn LOCALKAAM.wsgi:application --workers 2 --bind 0.0.0.0:$PORT --timeout 120
