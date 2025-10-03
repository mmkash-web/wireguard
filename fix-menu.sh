#!/bin/bash

# WireGuard MikroTik VPS Menu Fix Script
# This script fixes the menu system to work without Django

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

print_status "Fixing WireGuard MikroTik VPS Menu System..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Install Supabase if not already installed
print_status "Installing Supabase Python client..."
pip3 install supabase

# Create config directory
print_status "Creating configuration directory..."
mkdir -p /opt/wireguard-mikrotik-vps/config

# Create Supabase configuration template
print_status "Creating Supabase configuration template..."
cat > /opt/wireguard-mikrotik-vps/config/supabase.json << 'EOF'
{
  "url": "",
  "key": "",
  "table": "routers"
}
EOF

# Test the menu system
print_status "Testing the menu system..."
cd /opt/wireguard-mikrotik-vps

# Test if the menu can start without errors
python3 -c "
import sys
sys.path.append('/opt/wireguard-mikrotik-vps/menu')
from wireguard_menu import WireGuardMenu
menu = WireGuardMenu()
print('Menu system initialized successfully!')
print('Available data sources:')
print('  - WireGuard Configuration: ✓')
print('  - Supabase Database:', '✓' if menu.supabase.available else '✗ (not configured)')
print('  - Django Database:', '✓' if hasattr(menu, 'wg_service') and menu.wg_service else '✗ (not available)')
"

print_success "Menu system fixed successfully!"
print_status "The menu now works with:"
echo "  ✓ Local WireGuard configuration (always available)"
echo "  ✓ Supabase database (when configured)"
echo "  ✓ Django database (if available)"

print_warning "To configure Supabase integration:"
echo "1. Edit /opt/wireguard-mikrotik-vps/config/supabase.json"
echo "2. Add your Supabase URL and API key"
echo "3. Or set environment variables:"
echo "   export SUPABASE_URL='https://your-project.supabase.co'"
echo "   export SUPABASE_KEY='your-supabase-anon-key'"

print_status "You can now run the menu with: wg-menu"
