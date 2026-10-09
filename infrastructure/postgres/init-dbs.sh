#!/bin/bash
set -e

if ! psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw ssks_db; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE ssks_db;
EOSQL
fi
