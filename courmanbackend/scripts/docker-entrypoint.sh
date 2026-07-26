#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py seed_roles
python manage.py seed_admin
python manage.py collectstatic --noinput

exec "$@"
