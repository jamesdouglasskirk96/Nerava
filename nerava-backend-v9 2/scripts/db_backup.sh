#!/bin/bash

# Database backup script for Nerava
# Usage: ./scripts/db_backup.sh [backup_name]

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_URL="${DATABASE_URL:-sqlite:///./nerava.db}"
BACKUP_NAME="${1:-nerava_backup_$(date +%Y%m%d_%H%M%S)}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting database backup: $BACKUP_NAME"

# Function to backup PostgreSQL
backup_postgresql() {
    local db_url="$1"
    local backup_file="$2"
    
    # Extract connection details from DATABASE_URL
    # Format: postgresql://user:password@host:port/database
    local db_info=$(echo "$db_url" | sed 's|postgresql://||')
    local user=$(echo "$db_info" | cut -d: -f1)
    local password=$(echo "$db_info" | cut -d: -f2 | cut -d@ -f1)
    local host=$(echo "$db_info" | cut -d@ -f2 | cut -d: -f1)
    local port=$(echo "$db_info" | cut -d: -f3 | cut -d/ -f1)
    local database=$(echo "$db_info" | cut -d/ -f2)
    
    echo "Backing up PostgreSQL database: $database@$host:$port"
    
    # Set PGPASSWORD for non-interactive backup
    export PGPASSWORD="$password"
    
    # Create backup using pg_dump
    pg_dump -h "$host" -p "$port" -U "$user" -d "$database" \
        --verbose --no-password --format=custom --compress=9 \
        --file="$backup_file"
    
    unset PGPASSWORD
}

# Function to backup SQLite
backup_sqlite() {
    local db_url="$1"
    local backup_file="$2"
    
    # Extract database file path from SQLite URL
    local db_file=$(echo "$db_url" | sed 's|sqlite:///||')
    
    echo "Backing up SQLite database: $db_file"
    
    # Create backup using sqlite3
    sqlite3 "$db_file" ".backup '$backup_file'"
}

# Function to backup MySQL
backup_mysql() {
    local db_url="$1"
    local backup_file="$2"
    
    # Extract connection details from DATABASE_URL
    # Format: mysql://user:password@host:port/database
    local db_info=$(echo "$db_url" | sed 's|mysql://||')
    local user=$(echo "$db_info" | cut -d: -f1)
    local password=$(echo "$db_info" | cut -d: -f2 | cut -d@ -f1)
    local host=$(echo "$db_info" | cut -d@ -f2 | cut -d: -f1)
    local port=$(echo "$db_info" | cut -d: -f3 | cut -d/ -f1)
    local database=$(echo "$db_info" | cut -d/ -f2)
    
    echo "Backing up MySQL database: $database@$host:$port"
    
    # Create backup using mysqldump
    mysqldump -h "$host" -P "$port" -u "$user" -p"$password" \
        --single-transaction --routines --triggers \
        "$database" > "$backup_file"
}

# Determine database type and perform backup
if [[ "$DB_URL" == postgresql://* ]]; then
    backup_file="$BACKUP_DIR/${BACKUP_NAME}.sql.gz"
    backup_postgresql "$DB_URL" "$backup_file"
elif [[ "$DB_URL" == sqlite://* ]]; then
    backup_file="$BACKUP_DIR/${BACKUP_NAME}.db"
    backup_sqlite "$DB_URL" "$backup_file"
elif [[ "$DB_URL" == mysql://* ]]; then
    backup_file="$BACKUP_DIR/${BACKUP_NAME}.sql"
    backup_mysql "$DB_URL" "$backup_file"
else
    echo "Error: Unsupported database type in DATABASE_URL: $DB_URL"
    exit 1
fi

# Verify backup file was created and has content
if [[ -f "$backup_file" && -s "$backup_file" ]]; then
    backup_size=$(du -h "$backup_file" | cut -f1)
    echo "Backup completed successfully: $backup_file ($backup_size)"
else
    echo "Error: Backup file was not created or is empty"
    exit 1
fi

# Clean up old backups (retention policy)
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "nerava_backup_*" -type f -mtime +$RETENTION_DAYS -delete

# List current backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/nerava_backup_* 2>/dev/null || echo "No backups found"

echo "Database backup completed successfully"
