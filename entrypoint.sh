#!/bin/bash
set -e

echo "=== GameShelf Container Starting ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL database connection..."
python - << 'EOF'
import time
import os
import sys
import psycopg2

host = os.environ.get("POSTGRES_HOST", "db")
port = os.environ.get("POSTGRES_PORT", "5432")
user = os.environ.get("POSTGRES_USER", "gameshelf_user")
password = os.environ.get("POSTGRES_PASSWORD", "gameshelf_secure_password_2026")
dbname = os.environ.get("POSTGRES_DB", "gameshelf_db")

retries = 30
connected = False
while retries > 0:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=3
        )
        conn.close()
        connected = True
        print("Connected to PostgreSQL successfully.")
        break
    except Exception as e:
        retries -= 1
        print(f"Waiting for database... ({retries} retries left): {e}")
        time.sleep(1)

if not connected:
    print("Error: Could not connect to database after multiple retries.")
    sys.exit(1)
EOF

echo "Initializing database schema and initial data..."
python cli.py init-db
python cli.py seed-data

echo "Starting GameShelf application server on port 5000..."
exec gunicorn --bind 0.0.0.0:5000 --workers 3 --threads 2 --access-logfile - --error-logfile - "run:app"

