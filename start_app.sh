#!/bin/sh
set -e  # Exit on error

echo "run migration"
alembic upgrade head

echo "run gunicorn"
gunicorn -c gunicorn.conf.py src.main:app 