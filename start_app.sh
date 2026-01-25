#!/bin/sh
set -e  # Exit on error

echo "run migration"
alembic upgrade head

echo "run uvicorn"
uvicorn src.main:app --host 0.0.0.0 --port 8000 --loop uvloop