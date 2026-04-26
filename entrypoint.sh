#!/bin/sh
set -e

echo "Waiting for database connectivity..."
python wait_for_db.py

if [ "${SKIP_DB_MIGRATIONS}" != "1" ]; then
	echo "Applying database migrations..."
	flask db upgrade
fi

echo "Starting API server"
exec "$@"
