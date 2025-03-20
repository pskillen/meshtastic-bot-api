#!/bin/bash

export PGPASSWORD=meshtastic
pg_dump -h meshcontrol.local -U meshtastic -d meshtastic -F c -b -v -f remote_db_dump.sql

export PGPASSWORD=meshtastic
psql -h localhost -U meshtastic -d meshtastic -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
pg_restore -h localhost -U meshtastic -d meshtastic -v remote_db_dump.sql