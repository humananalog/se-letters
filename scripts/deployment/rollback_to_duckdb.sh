#!/bin/bash
# Rollback to DuckDB Script

set -e

echo "🔄 Rolling back to DuckDB..."

# Stop webapp if running
pkill -f "npm run dev" 2>/dev/null || true

# Restore DuckDB backup if exists
if [ -f "data/letters.duckdb.backup" ]; then
    echo "📦 Restoring DuckDB backup..."
    cp data/letters.duckdb.backup data/letters.duckdb
    echo "✅ DuckDB backup restored"
else
    echo "⚠️ No DuckDB backup found"
fi

# Update configuration to use DuckDB
echo "📝 Updating configuration..."
# Add configuration update logic here

echo "✅ Rollback completed!"
echo "🔄 Please restart the application to use DuckDB"
