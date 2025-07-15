#!/bin/bash

# SE Letters - Restart Application Script
# This script stops all processes and then starts the application

echo "🔄 SE LETTERS - RESTART APPLICATION"
echo "==================================="

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Step 1: Stop all processes
print_status "🛑 Stopping all processes..."
"$SCRIPT_DIR/stop_app.sh"

# Step 2: Wait a moment
print_status "⏳ Waiting before restart..."
sleep 2

# Step 3: Start the application
print_success "🚀 Starting application..."
"$SCRIPT_DIR/start_app.sh" 