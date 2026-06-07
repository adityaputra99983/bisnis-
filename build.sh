# Build script untuk Heroku-style deployment
# (Hostinger shared hosting: skip ini. Vercel: skip ini. Heroku/Render/Railway: jalan otomatis)

set -e

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Build complete ==="
