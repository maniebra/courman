#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py seed_roles
python manage.py seed_admin
python manage.py collectstatic --noinput

if [ "$(echo "${DJANGO_DEBUG:-false}" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    exec "$@"
fi

exec gunicorn courmanbackend.asgi:application \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    -w "${GUNICORN_WORKERS:-3}"
