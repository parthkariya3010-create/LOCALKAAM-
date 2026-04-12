release: python manage.py migrate --skip-checks --no-input 2>/dev/null || true
web: ENVIRONMENT=production gunicorn LOCALKAAM.wsgi:application --workers 2 --bind 0.0.0.0:$PORT --timeout 120
