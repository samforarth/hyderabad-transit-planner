#!/bin/bash
set -e

echo "⏳ Waiting for MySQL to be ready..."
until python -c "
import pymysql
pymysql.connect(host='${DB_HOST}', port=int('${DB_PORT}'), user='${DB_USER}', password='${DB_PASSWORD}')
" 2>/dev/null; do
    sleep 2
    echo "  ...still waiting"
done

echo "✅ MySQL is ready"

# Create database if it doesn't exist
python -c "
import pymysql
conn = pymysql.connect(host='${DB_HOST}', port=int('${DB_PORT}'), user='${DB_USER}', password='${DB_PASSWORD}')
cursor = conn.cursor()
cursor.execute('CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
conn.commit()
conn.close()
print('✅ Database ready')
"

# Check if data is already imported
NEEDS_IMPORT=$(python -c "
import pymysql
try:
    conn = pymysql.connect(host='${DB_HOST}', port=int('${DB_PORT}'), user='${DB_USER}', password='${DB_PASSWORD}', database='${DB_NAME}')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM stops')
    count = cursor.fetchone()[0]
    conn.close()
    print('no' if count > 0 else 'yes')
except:
    print('yes')
" 2>/dev/null)

if [ "$NEEDS_IMPORT" = "yes" ]; then
    echo "📦 Importing GTFS data (first run only, takes ~2 min)..."
    python import_gtfs.py
    echo "🚌 Importing IITH bus schedules..."
    python import_iith_buses.py
else
    echo "ℹ️  Data already imported, skipping."
fi

echo "🚀 Starting backend server..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
