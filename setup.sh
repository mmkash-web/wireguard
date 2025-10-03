#!/bin/bash

# WireGuard MikroTik VPS Quick Setup Script
# This script sets up the complete WireGuard MikroTik management system

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting WireGuard MikroTik VPS Setup..."

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install Python and pip
print_status "Installing Python and pip..."
apt install -y python3 python3-pip python3-venv

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install -r requirements.txt

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/*.sh
chmod +x menu/*.py
chmod +x tools/*.py

# Install WireGuard
print_status "Installing WireGuard..."
bash scripts/install-wireguard-vps.sh

# Create systemd service for menu
print_status "Creating systemd service..."
cat > /etc/systemd/system/wireguard-menu.service << 'EOF'
[Unit]
Description=WireGuard MikroTik Management Menu
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wireguard-mikrotik-vps
ExecStart=/usr/bin/python3 /opt/wireguard-mikrotik-vps/menu/wireguard-menu.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create symlinks for easy access
print_status "Creating symlinks..."
ln -sf /opt/wireguard-mikrotik-vps/menu/wireguard-menu.py /usr/local/bin/wg-menu
ln -sf /opt/wireguard-mikrotik-vps/menu/wireguard-dashboard.py /usr/local/bin/wg-dashboard
ln -sf /opt/wireguard-mikrotik-vps/tools/test-wireguard-setup.py /usr/local/bin/wg-test

# Create desktop entry (if desktop environment exists)
if [ -d "/usr/share/applications" ]; then
    print_status "Creating desktop entry..."
    cat > /usr/share/applications/wireguard-mikrotik.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=WireGuard MikroTik Manager
Comment=Manage WireGuard VPN with MikroTik routers
Exec=sudo python3 /opt/wireguard-mikrotik-vps/menu/wireguard-menu.py
Icon=network-wireless
Terminal=true
Categories=Network;System;
EOF
fi

# Set proper permissions
print_status "Setting permissions..."
chown -R root:root /opt/wireguard-mikrotik-vps
chmod -R 755 /opt/wireguard-mikrotik-vps

# Create log directory
mkdir -p /var/log/wireguard-mikrotik
chmod 755 /var/log/wireguard-mikrotik

print_success "Setup completed successfully!"
echo ""
echo "=========================================="
echo "WireGuard MikroTik VPS Setup Complete"
echo "=========================================="
echo ""
echo "Quick Commands:"
echo "  wg-menu        - Open management menu"
echo "  wg-dashboard   - Open real-time dashboard"
echo "  wg-test        - Run system test"
echo "  wg-status      - Check system status"
echo ""
echo "Next Steps:"
echo "1. Generate router configs:"
echo "   ./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_KEY -c 10"
echo ""
echo "2. Configure your MikroTik routers with the generated .rsc files"
echo ""
echo "3. Add routers to VPS:"
echo "   wg-mikrotik add router1 <public_key> 10.10.0.2"
echo ""
echo "4. Start managing:"
echo "   wg-menu"
echo ""
echo "Documentation:"
echo "  /opt/wireguard-mikrotik-vps/docs/"
echo "=========================================="
