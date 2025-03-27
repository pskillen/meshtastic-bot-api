#!/bin/bash

# Source database configuration
SOURCE_USER=meshtastic
SOURCE_PASSWORD=meshtastic
SOURCE_HOST=meshcontrol.local
SOURCE_DB=meshtastic

# Destination database configuration
DEST_USER=meshtastic_preprod
DEST_PASSWORD=Headway-Durably-Cargo1
DEST_HOST=docker-1
DEST_DB=meshtastic_preprod

# Export source password for pg_dump
export PGPASSWORD=$SOURCE_PASSWORD

# Dump the source database
pg_dump -h $SOURCE_HOST -U $SOURCE_USER -d $SOURCE_DB -F c -b -v -f remote_db_dump.sql

# Export destination password for psql and pg_restore
export PGPASSWORD=$DEST_PASSWORD

# Check if the destination database exists, and create it if it does not
psql -h $DEST_HOST -U $DEST_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '${DEST_DB}'" \
  | grep -q 1 \
  || psql -h $DEST_HOST -U $DEST_USER -d postgres -c "CREATE DATABASE ${DEST_DB};"

# Drop and recreate the public schema in the destination database
psql -h $DEST_HOST -U $DEST_USER -d $DEST_DB -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Restore the dump to the destination preprod database
pg_restore -h $DEST_HOST -U $DEST_USER -d $DEST_DB --no-owner --role=$DEST_USER -v remote_db_dump.sql
