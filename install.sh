#!/bin/bash

# WireGuard MikroTik VPS One-Command Installer
# This script can be run directly from GitHub for easy deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  WireGuard MikroTik VPS Installer${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo
}

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

print_header

# Configuration
REPO_URL="https://github.com/mmkash-web/wireguard.git"
INSTALL_DIR="/opt/wireguard-mikrotik-vps"

print_status "Starting WireGuard MikroTik VPS installation..."

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing required packages..."
apt install -y git curl wget python3 python3-pip python3-venv

# Clone repository
print_status "Cloning repository from GitHub..."
if [ -d "$INSTALL_DIR" ]; then
    print_warning "Installation directory exists. Backing up..."
    mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Set proper permissions
print_status "Setting permissions..."
chown -R root:root .
chmod +x scripts/*.sh
chmod +x menu/*.py
chmod +x tools/*.py

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install WireGuard
print_status "Installing WireGuard..."
bash scripts/install-wireguard-vps.sh

# Create symlinks for easy access
print_status "Creating command symlinks..."
ln -sf "$INSTALL_DIR/menu/wireguard-menu.py" /usr/local/bin/wg-menu
ln -sf "$INSTALL_DIR/menu/wireguard-dashboard.py" /usr/local/bin/wg-dashboard
ln -sf "$INSTALL_DIR/tools/test-wireguard-setup.py" /usr/local/bin/wg-test

# Create systemd service
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

# Create log directory
mkdir -p /var/log/wireguard-mikrotik
chmod 755 /var/log/wireguard-mikrotik

# Get VPS public key
VPS_PUBLIC_KEY=$(cat /etc/wireguard/keys/server_public.key 2>/dev/null || echo "NOT_FOUND")

print_success "Installation completed successfully!"
echo
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Installation Complete!${NC}"
echo -e "${CYAN}========================================${NC}"
echo
echo -e "${GREEN}Quick Commands:${NC}"
echo "  wg-menu        - Open management menu"
echo "  wg-dashboard   - Open real-time dashboard"
echo "  wg-test        - Run system test"
echo "  wg-status      - Check system status"
echo
echo -e "${GREEN}VPS Public Key:${NC}"
if [ "$VPS_PUBLIC_KEY" != "NOT_FOUND" ]; then
    echo "$VPS_PUBLIC_KEY"
else
    echo "Key not found. Check /etc/wireguard/keys/"
fi
echo
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Generate router configs:"
echo "   cd $INSTALL_DIR"
echo "   ./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k $VPS_PUBLIC_KEY -c 10"
echo
echo "2. Configure your MikroTik routers with the generated .rsc files"
echo
echo "3. Add routers to VPS:"
echo "   wg-mikrotik add router1 <public_key> 10.10.0.2"
echo
echo "4. Start managing:"
echo "   wg-menu"
echo
echo -e "${GREEN}Documentation:${NC}"
echo "  $INSTALL_DIR/docs/"
echo -e "${CYAN}========================================${NC}"

# Ask if user wants to generate router configs now
echo
read -p "Would you like to generate router configurations now? (y/N): " generate_configs

if [[ $generate_configs =~ ^[Yy]$ ]]; then
    echo
    read -p "Enter your VPS public IP address: " vps_ip
    read -p "Number of routers to generate (default 5): " router_count
    
    if [ -z "$router_count" ]; then
        router_count=5
    fi
    
    if [ -n "$vps_ip" ] && [ "$VPS_PUBLIC_KEY" != "NOT_FOUND" ]; then
        print_status "Generating router configurations..."
        ./scripts/mikrotik-wireguard-setup.sh -v "$vps_ip" -k "$VPS_PUBLIC_KEY" -c "$router_count"
        print_success "Router configurations generated in configs/ directory"
    else
        print_warning "Skipping router config generation. You can run it later with:"
        echo "  ./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k $VPS_PUBLIC_KEY -c 10"
    fi
fi

echo
print_success "Installation complete! Your WireGuard MikroTik VPS is ready! 🎉"
