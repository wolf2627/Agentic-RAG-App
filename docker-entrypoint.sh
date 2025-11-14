#!/bin/sh

set -eu

cd /app

# Check if there are documents to index
if [ -d "/app/documents" ] && [ "$(ls -A /app/documents)" ]; then
  echo "[entrypoint] Ingesting documents..."
  make index || echo "[entrypoint] Warning: Document indexing failed, but continuing..."
else
  echo "[entrypoint] No documents found in /app/documents, skipping indexing"
fi

echo "[entrypoint] Starting API server..."
exec make dev
