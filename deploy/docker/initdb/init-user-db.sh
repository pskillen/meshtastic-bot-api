#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER meshtastic WITH PASSWORD 'meshtastic';
    CREATE DATABASE meshtastic;
    GRANT ALL PRIVILEGES ON DATABASE meshtastic TO meshtastic;
    ALTER USER meshtastic WITH SUPERUSER;
EOSQL
