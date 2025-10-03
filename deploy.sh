#!/bin/bash

# WireGuard MikroTik VPS Deployment Script
# This script deploys the project to a VPS

set -e

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

# Configuration
VPS_IP=""
VPS_USER="root"
PROJECT_DIR="/opt/wireguard-mikrotik-vps"

# Function to show usage
show_usage() {
    echo "WireGuard MikroTik VPS Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -v, --vps-ip IP          VPS IP address (required)"
    echo "  -u, --user USER          VPS username (default: root)"
    echo "  -d, --dir DIRECTORY      Project directory on VPS (default: /opt/wireguard-mikrotik-vps)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -v 203.0.113.1"
    echo "  $0 -v 203.0.113.1 -u admin -d /home/admin/wireguard"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--vps-ip)
            VPS_IP="$2"
            shift 2
            ;;
        -u|--user)
            VPS_USER="$2"
            shift 2
            ;;
        -d|--dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$VPS_IP" ]; then
    print_error "VPS IP address is required"
    show_usage
    exit 1
fi

print_status "Starting deployment to VPS: $VPS_IP"
print_status "VPS User: $VPS_USER"
print_status "Project Directory: $PROJECT_DIR"

# Check if project directory exists
if [ ! -d "." ]; then
    print_error "Project directory not found. Please run from project root."
    exit 1
fi

# Create deployment package
print_status "Creating deployment package..."
TEMP_DIR=$(mktemp -d)
cp -r . "$TEMP_DIR/wireguard-mikrotik-vps"
cd "$TEMP_DIR"

# Remove unnecessary files
rm -rf wireguard-mikrotik-vps/.git
rm -rf wireguard-mikrotik-vps/__pycache__
rm -rf wireguard-mikrotik-vps/*/__pycache__
rm -rf wireguard-mikrotik-vps/.vscode
rm -rf wireguard-mikrotik-vps/.idea

# Create deployment archive
print_status "Creating deployment archive..."
tar -czf wireguard-mikrotik-vps.tar.gz wireguard-mikrotik-vps/

# Upload to VPS
print_status "Uploading to VPS..."
scp wireguard-mikrotik-vps.tar.gz "$VPS_USER@$VPS_IP:/tmp/"

# Deploy on VPS
print_status "Deploying on VPS..."
ssh "$VPS_USER@$VPS_IP" << EOF
    # Extract project
    cd /opt
    tar -xzf /tmp/wireguard-mikrotik-vps.tar.gz
    rm /tmp/wireguard-mikrotik-vps.tar.gz
    
    # Set permissions
    chown -R root:root wireguard-mikrotik-vps
    chmod -R 755 wireguard-mikrotik-vps
    
    # Make scripts executable
    chmod +x wireguard-mikrotik-vps/scripts/*.sh
    chmod +x wireguard-mikrotik-vps/menu/*.py
    chmod +x wireguard-mikrotik-vps/tools/*.py
    
    # Install dependencies
    apt update
    apt install -y python3 python3-pip
    pip3 install -r wireguard-mikrotik-vps/requirements.txt
    
    # Run setup
    cd wireguard-mikrotik-vps
    bash setup.sh
    
    echo "Deployment completed successfully!"
EOF

# Cleanup
rm -rf "$TEMP_DIR"

print_success "Deployment completed successfully!"
echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo "VPS IP: $VPS_IP"
echo "Project Directory: $PROJECT_DIR"
echo ""
echo "Next Steps:"
echo "1. SSH to your VPS:"
echo "   ssh $VPS_USER@$VPS_IP"
echo ""
echo "2. Navigate to project:"
echo "   cd $PROJECT_DIR"
echo ""
echo "3. Generate router configs:"
echo "   ./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_KEY -c 10"
echo ""
echo "4. Start management interface:"
echo "   wg-menu"
echo ""
echo "5. Or start real-time dashboard:"
echo "   wg-dashboard"
echo "=========================================="
