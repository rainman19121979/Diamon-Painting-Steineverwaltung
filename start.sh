#!/bin/bash

# Diamond Painting Manager - Startup Script
# This script starts the Flask application server

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    echo "Please run './install.sh' first to set up the application."
    exit 1
fi

# Check if app directory exists
if [ ! -d "app" ]; then
    print_error "Application directory 'app' not found!"
    exit 1
fi

# Activate virtual environment
print_message "Activating virtual environment..."
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    print_error "Flask is not installed in the virtual environment!"
    echo "Please run './install.sh' to install dependencies."
    exit 1
fi

# Set Flask environment variables
export FLASK_APP=app.app
export FLASK_ENV=development
export FLASK_DEBUG=1

# Configuration
HOST="0.0.0.0"
PORT="5000"

# Get container IP address
CONTAINER_IP=$(hostname -I | awk '{print $1}')

print_message "${BLUE}========================================${NC}"
print_message "${BLUE}Diamond Painting Manager${NC}"
print_message "${BLUE}========================================${NC}"
echo ""
print_message "Starting Flask server..."
print_message "Host: $HOST"
print_message "Port: $PORT"
echo ""
print_message "${GREEN}Application URLs:${NC}"
echo "  - Local:   http://localhost:$PORT"
echo "  - Network: http://$CONTAINER_IP:$PORT"
echo ""
print_warning "Press CTRL+C to stop the server"
echo ""

# Start Flask development server
# For production, consider using: gunicorn -w 4 -b 0.0.0.0:5000 app.app:app
python app/app.py

# This will only execute if the server stops
print_message "Server stopped."
