#!/bin/bash

# SE Letters - Clean Start Script
# This script cleans up all running processes and starts the application fresh

set -e  # Exit on any error

echo "🧹 SE LETTERS - CLEAN START SCRIPT"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

print_status "Project root: $PROJECT_ROOT"

# Step 1: Kill all Node.js/Next.js processes
print_status "🔪 Killing all Node.js/Next.js processes..."
if pgrep -f "next dev" > /dev/null; then
    pkill -f "next dev" && print_success "Killed Next.js dev servers" || print_warning "Some Next.js processes may still be running"
else
    print_status "No Next.js dev servers found"
fi

if pgrep -f "node.*webapp" > /dev/null; then
    pkill -f "node.*webapp" && print_success "Killed webapp Node processes" || print_warning "Some webapp processes may still be running"
else
    print_status "No webapp Node processes found"
fi

# Step 2: Kill all Python pipeline processes
print_status "🐍 Killing all Python pipeline processes..."
if pgrep -f "production_pipeline" > /dev/null; then
    pkill -f "production_pipeline" && print_success "Killed production pipeline processes" || print_warning "Some pipeline processes may still be running"
else
    print_status "No production pipeline processes found"
fi

if pgrep -f "se_letters" > /dev/null; then
    pkill -f "se_letters" && print_success "Killed se_letters processes" || print_warning "Some se_letters processes may still be running"
else
    print_status "No se_letters processes found"
fi

# Step 3: Clean up any processes using ports 3000-3002
print_status "🚪 Cleaning up ports 3000-3002..."
for port in 3000 3001 3002; do
    if lsof -ti:$port > /dev/null 2>&1; then
        print_status "Killing process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null && print_success "Port $port cleared" || print_warning "Could not clear port $port"
    else
        print_status "Port $port is free"
    fi
done

# Step 4: Clean up database locks
print_status "🗄️ Checking database locks..."
if lsof data/letters.duckdb 2>/dev/null; then
    print_warning "Database file is still locked, attempting to clear..."
    lsof data/letters.duckdb | awk 'NR>1 {print $2}' | xargs kill -9 2>/dev/null && print_success "Database locks cleared" || print_warning "Could not clear all database locks"
else
    print_success "No database locks found"
fi

# Step 5: Wait a moment for processes to fully terminate
print_status "⏳ Waiting for processes to terminate..."
sleep 3

# Step 6: Test database connection
print_status "🧪 Testing database connection..."
if python3 -c "import duckdb; conn = duckdb.connect('data/letters.duckdb'); print('✅ Database connection successful'); conn.close()" 2>/dev/null; then
    print_success "Database connection verified"
else
    print_error "Database connection failed - there may still be locks"
fi

# Step 7: Install/update dependencies
print_status "📦 Checking webapp dependencies..."
cd webapp
if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
    print_status "Installing/updating npm dependencies..."
    npm install
    print_success "Dependencies updated"
else
    print_status "Dependencies are up to date"
fi

# Step 8: Start the webapp
print_status "🚀 Starting the webapp..."
print_status "The webapp will start on the first available port (3000, 3001, or 3002)"
print_status "Press Ctrl+C to stop the server"
echo ""
print_success "🌟 Starting SE Letters webapp..."
echo ""

# Start the development server
npm run dev

# This line will only execute if npm run dev exits
print_warning "Webapp server stopped" 