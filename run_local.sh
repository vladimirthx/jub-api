#!/bin/bash
docker compose -f docker-compose.yml down jub-db || true
docker compose -f xolo.yml down || true
docker compose -f docker-compose.yml -p jub up jub-db -d
docker compose -f xolo.yml -p xolo up -d
uvicorn jubapi.server:app --host ${JUB_HOST:-0.0.0.0} --port ${JUB_PORT:-5000} --reload
