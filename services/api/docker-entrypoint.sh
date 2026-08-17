#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py sync_shared_exercise_bank

exec "$@"
