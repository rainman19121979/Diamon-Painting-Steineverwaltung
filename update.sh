#!/bin/bash

# Diamond Painting Manager - Update Script
# This script updates the application to the latest version from GitHub

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

print_message "${BLUE}========================================${NC}"
print_message "${BLUE}Diamond Painting Manager - Update${NC}"
print_message "${BLUE}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if this is a git repository
if [ ! -d ".git" ]; then
    print_error "Not a git repository!"
    echo "This update script only works if installed via git clone."
    echo ""
    echo "Manual update:"
    echo "  1. Backup your data directory"
    echo "  2. Download latest version from GitHub"
    echo "  3. Replace files (keep data/ directory)"
    exit 1
fi

# Check if service is running
SERVICE_RUNNING=false
if command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet diamond-painting 2>/dev/null; then
        SERVICE_RUNNING=true
        print_message "Service is currently running - will be restarted after update"
    fi
fi

# Backup important files
print_message "Creating backup..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup data and configuration
if [ -d "data" ]; then
    cp -r data "$BACKUP_DIR/"
    print_message "Backed up data directory"
fi

if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/"
    print_message "Backed up .env configuration"
fi

# Stop service if running
if [ "$SERVICE_RUNNING" = true ]; then
    print_message "Stopping service..."
    sudo systemctl stop diamond-painting
fi

# Fetch latest changes
print_message "Fetching latest version from GitHub..."
git fetch origin

# Check for changes
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ $LOCAL = $REMOTE ]; then
    print_message "Already up to date!"

    # Restart service if it was running
    if [ "$SERVICE_RUNNING" = true ]; then
        print_message "Restarting service..."
        sudo systemctl start diamond-painting
    fi

    exit 0
fi

# Show what will be updated
echo ""
print_message "Changes in new version:"
git log --oneline --decorate --graph HEAD..@{u}
echo ""

# Ask for confirmation
read -p "Continue with update? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Update cancelled"

    # Restart service if it was running
    if [ "$SERVICE_RUNNING" = true ]; then
        print_message "Restarting service..."
        sudo systemctl start diamond-painting
    fi

    exit 0
fi

# Pull latest changes
print_message "Updating files..."
git pull origin main

# Activate virtual environment
if [ -d "venv" ]; then
    print_message "Activating virtual environment..."
    source venv/bin/activate

    # Update dependencies
    print_message "Updating dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    deactivate
else
    print_warning "Virtual environment not found - skipping dependency update"
fi

# Restore configuration if it was backed up
if [ -f "$BACKUP_DIR/.env" ]; then
    print_message "Restoring .env configuration..."
    cp "$BACKUP_DIR/.env" .env
fi

# Update systemd service if running as root
if [ "$EUID" -eq 0 ] && command -v systemctl &> /dev/null; then
    if systemctl list-unit-files | grep -q diamond-painting.service; then
        print_message "Updating systemd service..."

        # Read port from .env
        if [ -f ".env" ]; then
            PORT=$(grep FLASK_PORT .env | cut -d '=' -f2)
        else
            PORT=8080
        fi

        INSTALL_DIR="$SCRIPT_DIR"
        cat > /etc/systemd/system/diamond-painting.service <<EOF
[Unit]
Description=Diamond Painting Organizer
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="FLASK_APP=app.app"
Environment="FLASK_PORT=$PORT"
Environment="FLASK_DEBUG=0"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/app/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
    fi
fi

# Restart service if it was running
if [ "$SERVICE_RUNNING" = true ]; then
    print_message "Starting service..."
    sudo systemctl start diamond-painting
    sleep 2
    systemctl status diamond-painting --no-pager
fi

print_message "${GREEN}========================================${NC}"
print_message "${GREEN}Update completed successfully!${NC}"
print_message "${GREEN}========================================${NC}"
echo ""
print_message "Backup created in: $BACKUP_DIR"
echo ""

if [ "$SERVICE_RUNNING" = true ]; then
    print_message "Service restarted automatically"
else
    print_message "Start the application:"
    echo "  ./start.sh"
    echo "  or"
    echo "  sudo systemctl start diamond-painting"
fi

echo ""
print_message "Happy Diamond Painting! ✨"
