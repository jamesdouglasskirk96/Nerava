#!/bin/bash

# Database restore script for Nerava
# Usage: ./scripts/db_restore.sh <backup_file> [--force]

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_URL="${DATABASE_URL:-sqlite:///./nerava.db}"
FORCE_RESTORE=false

# Parse arguments
BACKUP_FILE="$1"
if [[ "$2" == "--force" ]]; then
    FORCE_RESTORE=true
fi

# Validate arguments
if [[ -z "$BACKUP_FILE" ]]; then
    echo "Error: Backup file is required"
    echo "Usage: $0 <backup_file> [--force]"
    echo "Available backups:"
    ls -la "$BACKUP_DIR"/nerava_backup_* 2>/dev/null || echo "No backups found"
    exit 1
fi

# Check if backup file exists
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting database restore from: $BACKUP_FILE"

# Function to restore PostgreSQL
restore_postgresql() {
    local db_url="$1"
    local backup_file="$2"
    
    # Extract connection details from DATABASE_URL
    local db_info=$(echo "$db_url" | sed 's|postgresql://||')
    local user=$(echo "$db_info" | cut -d: -f1)
    local password=$(echo "$db_info" | cut -d: -f2 | cut -d@ -f1)
    local host=$(echo "$db_info" | cut -d@ -f2 | cut -d: -f1)
    local port=$(echo "$db_info" | cut -d: -f3 | cut -d/ -f1)
    local database=$(echo "$db_info" | cut -d/ -f2)
    
    echo "Restoring PostgreSQL database: $database@$host:$port"
    
    # Set PGPASSWORD for non-interactive restore
    export PGPASSWORD="$password"
    
    # Drop and recreate database if force restore
    if [[ "$FORCE_RESTORE" == "true" ]]; then
        echo "Force restore: Dropping and recreating database..."
        psql -h "$host" -p "$port" -U "$user" -d "postgres" -c "DROP DATABASE IF EXISTS $database;"
        psql -h "$host" -p "$port" -U "$user" -d "postgres" -c "CREATE DATABASE $database;"
    fi
    
    # Restore from backup
    pg_restore -h "$host" -p "$port" -U "$user" -d "$database" \
        --verbose --no-password --clean --if-exists \
        "$backup_file"
    
    unset PGPASSWORD
}

# Function to restore SQLite
restore_sqlite() {
    local db_url="$1"
    local backup_file="$2"
    
    # Extract database file path from SQLite URL
    local db_file=$(echo "$db_url" | sed 's|sqlite:///||')
    
    echo "Restoring SQLite database: $db_file"
    
    # Backup current database if it exists
    if [[ -f "$db_file" ]]; then
        local current_backup="${db_file}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Backing up current database to: $current_backup"
        cp "$db_file" "$current_backup"
    fi
    
    # Restore from backup
    cp "$backup_file" "$db_file"
}

# Function to restore MySQL
restore_mysql() {
    local db_url="$1"
    local backup_file="$2"
    
    # Extract connection details from DATABASE_URL
    local db_info=$(echo "$db_url" | sed 's|mysql://||')
    local user=$(echo "$db_info" | cut -d: -f1)
    local password=$(echo "$db_info" | cut -d: -f2 | cut -d@ -f1)
    local host=$(echo "$db_info" | cut -d@ -f2 | cut -d: -f1)
    local port=$(echo "$db_info" | cut -d: -f3 | cut -d/ -f1)
    local database=$(echo "$db_info" | cut -d/ -f2)
    
    echo "Restoring MySQL database: $database@$host:$port"
    
    # Drop and recreate database if force restore
    if [[ "$FORCE_RESTORE" == "true" ]]; then
        echo "Force restore: Dropping and recreating database..."
        mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "DROP DATABASE IF EXISTS $database;"
        mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "CREATE DATABASE $database;"
    fi
    
    # Restore from backup
    mysql -h "$host" -P "$port" -u "$user" -p"$password" "$database" < "$backup_file"
}

# Confirm restore operation
if [[ "$FORCE_RESTORE" != "true" ]]; then
    echo "WARNING: This will restore the database from backup."
    echo "Current database will be overwritten."
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled."
        exit 0
    fi
fi

# Determine database type and perform restore
if [[ "$DB_URL" == postgresql://* ]]; then
    restore_postgresql "$DB_URL" "$BACKUP_FILE"
elif [[ "$DB_URL" == sqlite://* ]]; then
    restore_sqlite "$DB_URL" "$BACKUP_FILE"
elif [[ "$DB_URL" == mysql://* ]]; then
    restore_mysql "$DB_URL" "$BACKUP_FILE"
else
    echo "Error: Unsupported database type in DATABASE_URL: $DB_URL"
    exit 1
fi

# Verify restore was successful
echo "Verifying restore..."

# Check if database is accessible
if [[ "$DB_URL" == postgresql://* ]]; then
    # Test PostgreSQL connection
    db_info=$(echo "$DB_URL" | sed 's|postgresql://||')
    user=$(echo "$db_info" | cut -d: -f1)
    password=$(echo "$db_info" | cut -d: -f2 | cut -d@ -f1)
    host=$(echo "$db_info" | cut -d@ -f2 | cut -d: -f1)
    port=$(echo "$db_info" | cut -d: -f3 | cut -d/ -f1)
    database=$(echo "$db_info" | cut -d/ -f2)
    
    export PGPASSWORD="$password"
    if psql -h "$host" -p "$port" -U "$user" -d "$database" -c "SELECT 1;" > /dev/null 2>&1; then
        echo "PostgreSQL restore verification successful"
    else
        echo "Error: PostgreSQL restore verification failed"
        exit 1
    fi
    unset PGPASSWORD
    
elif [[ "$DB_URL" == sqlite://* ]]; then
    # Test SQLite database
    db_file=$(echo "$DB_URL" | sed 's|sqlite:///||')
    if sqlite3 "$db_file" "SELECT 1;" > /dev/null 2>&1; then
        echo "SQLite restore verification successful"
    else
        echo "Error: SQLite restore verification failed"
        exit 1
    fi
    
elif [[ "$DB_URL" == mysql://* ]]; then
    # Test MySQL connection
    db_info=$(echo "$DB_URL" | sed 's|mysql://||')
    user=$(echo "$db_info" | cut -d: -f1)
    password=$(echo "$db_info" | cut -d: -f2 | cut -d@ -f1)
    host=$(echo "$db_info" | cut -d@ -f2 | cut -d: -f1)
    port=$(echo "$db_info" | cut -d: -f3 | cut -d/ -f1)
    database=$(echo "$db_info" | cut -d/ -f2)
    
    if mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SELECT 1;" > /dev/null 2>&1; then
        echo "MySQL restore verification successful"
    else
        echo "Error: MySQL restore verification failed"
        exit 1
    fi
fi

echo "Database restore completed successfully"
