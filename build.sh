
#!/usr/bin/env bash
set -o errexit

echo "──────────────────────────────────────────"
echo "  AstroGyan API — Render Build Script"
echo "──────────────────────────────────────────"

echo "→ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "→ Collecting static files..."
python manage.py collectstatic --no-input

echo "→ Running migrations..."
python manage.py migrate --no-input

echo "✓ Build complete"
