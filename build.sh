#!/usr/bin/env bash
# =============================================================================
# build.sh  —  Render.com build script for Bureau Auto Trading (Django)
# Place at the ROOT of your repo and make executable: chmod +x build.sh
# =============================================================================

set -o errexit
set -o pipefail

echo "-----> Installing Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "-----> Collecting static files (WhiteNoise)"
python manage.py collectstatic --no-input --clear

echo "-----> Applying database migrations"
python manage.py migrate --no-input
python manage.py populate_db

# ---------------------------------------------------------------------------
# Optional: auto-create a superuser on first deploy.
# Set in Render dashboard → Environment:
#   DJANGO_SUPERUSER_USERNAME
#   DJANGO_SUPERUSER_EMAIL
#   DJANGO_SUPERUSER_PASSWORD
# ---------------------------------------------------------------------------
if [[ -n "$DJANGO_SUPERUSER_USERNAME" ]]; then
    echo "-----> Creating superuser"
    python manage.py createsuperuser --no-input || true
fi

echo "-----> Build complete ✓"