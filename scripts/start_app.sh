#!/bin/bash

# SE Letters - Clean Start Script (PostgreSQL Version)
# This script cleans up all running processes and starts the application fresh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Load environment variables from .env file
if [ -f .env ]; then
    print_status "📄 Loading environment variables from .env file..."
    set -o allexport
    source .env
    set +o allexport
    print_success "Environment variables loaded"
else
    print_warning ".env file not found"
fi

# Step 1: Check environment variables
print_status "🔧 Checking environment variables..."
if [ -z "$XAI_API_KEY" ]; then
    print_error "XAI_API_KEY environment variable is not set"
    print_status "Please set it: export XAI_API_KEY='your-api-key'"
    exit 1
else
    print_success "XAI_API_KEY is set"
fi

if [ -z "$DATABASE_URL" ]; then
    print_warning "DATABASE_URL not set, using default PostgreSQL connection"
    export DATABASE_URL="postgresql://se_letters_user:se_letters_password@localhost:5432/se_letters_dev"
else
    print_success "DATABASE_URL is set"
fi

# Step 2: Kill all Node.js/Next.js processes
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

# Step 3: Kill all Python pipeline processes
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

# Step 4: Clean up any processes using ports 3000-3002
print_status "🚪 Cleaning up ports 3000-3002..."
for port in 3000 3001 3002; do
    if lsof -ti:$port > /dev/null 2>&1; then
        print_status "Killing process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null && print_success "Port $port cleared" || print_warning "Could not clear port $port"
    else
        print_status "Port $port is free"
    fi
done

# Step 5: Check PostgreSQL service status
print_status "🗄️ Checking PostgreSQL service..."
if command -v brew &> /dev/null; then
    # macOS with Homebrew
    if brew services list | grep -q 'postgresql.*started'; then
        print_success "PostgreSQL service is running"
    else
        print_warning "PostgreSQL service is not running"
        print_status "Starting PostgreSQL service..."
        brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null
        sleep 3
        if brew services list | grep -q 'postgresql.*started'; then
            print_success "PostgreSQL service started successfully"
        else
            print_error "Failed to start PostgreSQL service"
            print_status "Please start PostgreSQL manually: brew services start postgresql"
            exit 1
        fi
    fi
elif command -v systemctl &> /dev/null; then
    # Linux with systemd
    if systemctl is-active --quiet postgresql; then
        print_success "PostgreSQL service is running"
    else
        print_warning "PostgreSQL service is not running"
        print_status "Starting PostgreSQL service..."
        sudo systemctl start postgresql
        sleep 3
        if systemctl is-active --quiet postgresql; then
            print_success "PostgreSQL service started successfully"
        else
            print_error "Failed to start PostgreSQL service"
            print_status "Please start PostgreSQL manually: sudo systemctl start postgresql"
            exit 1
        fi
    fi
else
    print_warning "Could not detect PostgreSQL service manager"
    print_status "Please ensure PostgreSQL is running manually"
fi

# Step 6: Test PostgreSQL connection
print_status "🧪 Testing PostgreSQL connection..."
if python3 -c "import psycopg2, os; conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgresql://se_letters_user:se_letters_password@localhost:5432/se_letters_dev')); print('✅ PostgreSQL connection successful'); conn.close()" 2>/dev/null; then
    print_success "PostgreSQL connection verified"
else
    print_error "PostgreSQL connection failed"
    print_status "Please check your PostgreSQL setup and DATABASE_URL"
    print_status "Expected format: postgresql://username:password@host:port/database"
    exit 1
fi

# Step 7: Wait a moment for processes to fully terminate
print_status "⏳ Waiting for processes to terminate..."
sleep 3

# Step 8: Install/update dependencies
print_status "📦 Checking webapp dependencies..."
cd webapp
if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
    print_status "Installing/updating npm dependencies..."
    npm install
    print_success "Dependencies updated"
else
    print_status "Dependencies are up to date"
fi

# Step 9: Start the webapp
print_status "🚀 Starting the webapp..."
print_status "The webapp will start on the first available port (3000, 3001, or 3002)"
print_status "Press Ctrl+C to stop the server"
echo ""
print_success "🌟 Starting SE Letters webapp (PostgreSQL)..."
echo ""

# Start the development server
npm run dev

# This line will only execute if npm run dev exits
print_warning "Webapp server stopped" 