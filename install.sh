#!/bin/bash

# Diamond Painting Manager - Installation Script
# This script sets up the Flask application in a Proxmox LXC container

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

print_message "Starting Diamond Painting Manager installation..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. Creating venv as current user is recommended."
fi

# Check Python version
print_message "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    echo "Please install Python 3 using: apt-get update && apt-get install -y python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
print_message "Found Python $PYTHON_VERSION"

if ! command -v python3-venv &> /dev/null; then
    print_warning "python3-venv not found. Attempting to install..."
    if [ "$EUID" -eq 0 ]; then
        apt-get update
        apt-get install -y python3-venv
    else
        print_error "Please install python3-venv: sudo apt-get install -y python3-venv"
        exit 1
    fi
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in $SCRIPT_DIR"
    exit 1
fi

# Remove old virtual environment if it exists
if [ -d "venv" ]; then
    print_warning "Existing virtual environment found. Removing..."
    rm -rf venv
fi

# Create virtual environment
print_message "Creating virtual environment..."
python3 -m venv venv

if [ ! -d "venv" ]; then
    print_error "Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
print_message "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_message "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_message "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

# Create data directory structure
print_message "Creating application directories..."
mkdir -p data
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/templates

# Set proper permissions
print_message "Setting permissions..."
chmod -R 755 app/
chmod -R 755 data/
chmod +x start.sh 2>/dev/null || true

# Create initial data file if it doesn't exist
if [ ! -f "data/stones.json" ]; then
    print_message "Creating initial data file..."
    echo "[]" > data/stones.json
fi

# Install systemd service (if root and systemd is available)
if [ "$EUID" -eq 0 ] && command -v systemctl &> /dev/null; then
    print_message "Installing systemd service..."

    # Update service file paths
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
Environment="FLASK_ENV=production"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/app/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable diamond-painting.service

    print_message "Systemd service installed and enabled!"
    echo ""
    print_message "Service Management Commands:"
    echo "  systemctl start diamond-painting    - Start the service"
    echo "  systemctl stop diamond-painting     - Stop the service"
    echo "  systemctl restart diamond-painting  - Restart the service"
    echo "  systemctl status diamond-painting   - Check service status"
    echo "  journalctl -u diamond-painting -f   - View live logs"
    echo ""

    # Ask if service should be started now
    read -p "Start the service now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl start diamond-painting
        sleep 2
        systemctl status diamond-painting --no-pager
    fi
else
    if [ "$EUID" -ne 0 ]; then
        print_warning "Not running as root - systemd service not installed"
        print_message "To install as systemd service, run: sudo ./install.sh"
    fi
fi

print_message "${GREEN}========================================${NC}"
print_message "${GREEN}Installation completed successfully!${NC}"
print_message "${GREEN}========================================${NC}"
echo ""

if [ "$EUID" -ne 0 ] || ! command -v systemctl &> /dev/null; then
    print_message "Manual start:"
    echo "  ./start.sh"
    echo ""
fi

print_message "Access the application at:"
echo "  http://localhost:5000"
echo "  http://YOUR_LXC_IP:5000"
echo ""
print_message "Happy Diamond Painting! ✨"
