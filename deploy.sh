#!/bin/bash
readonly env_file=${1:-".env.dev"}
docker volume create xolo-db > /dev/null 2>&1 || true
docker network create jub > /dev/null 2>&1 || true

echo "Using environment file: $env_file"
docker compose -p jub --env-file "$env_file" -f docker-compose.yml down
docker compose -p jub --env-file "$env_file" -f docker-compose.yml up -d --build

docker compose -p jub --env-file "$env_file" -f xolo.yml down
docker compose -p jub --env-file "$env_file" -f xolo.yml up -d
