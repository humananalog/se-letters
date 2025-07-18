#!/bin/bash
# PostgreSQL Backup Script

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="data/backups"
BACKUP_FILE="$BACKUP_DIR/se_letters_postgresql_$TIMESTAMP.sql"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Set PostgreSQL path
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

echo "📦 Creating PostgreSQL backup: $BACKUP_FILE"

# Create backup
pg_dump -h localhost -U alexandre -d se_letters_dev -f "$BACKUP_FILE" --verbose

echo "✅ Backup created successfully: $BACKUP_FILE"
echo "📊 Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
