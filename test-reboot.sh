#!/bin/bash

# WireGuard MikroTik VPS Reboot Test
# This script simulates a reboot and checks if services start correctly

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

print_status "Testing WireGuard MikroTik VPS Reboot Readiness..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

echo "=========================================="
echo "REBOOT READINESS TEST"
echo "=========================================="

# 1. Check if services are enabled
print_status "Checking enabled services..."

services_ok=true

# Check WireGuard service
if systemctl is-enabled wireguard-mikrotik.service >/dev/null 2>&1; then
    echo -e "  wireguard-mikrotik.service: ${GREEN}✓ Enabled${NC}"
else
    echo -e "  wireguard-mikrotik.service: ${RED}✗ Not enabled${NC}"
    services_ok=false
fi

# Check startup service
if systemctl is-enabled wireguard-startup.service >/dev/null 2>&1; then
    echo -e "  wireguard-startup.service: ${GREEN}✓ Enabled${NC}"
else
    echo -e "  wireguard-startup.service: ${YELLOW}○ Not enabled (optional)${NC}"
fi

# Check monitoring timer
if systemctl is-enabled wireguard-monitor.timer >/dev/null 2>&1; then
    echo -e "  wireguard-monitor.timer: ${GREEN}✓ Enabled${NC}"
else
    echo -e "  wireguard-monitor.timer: ${YELLOW}○ Not enabled (optional)${NC}"
fi

# 2. Check configuration files
print_status "Checking configuration files..."

config_ok=true

# Check WireGuard config
if [ -f "/etc/wireguard/wg0.conf" ]; then
    echo -e "  WireGuard config: ${GREEN}✓ Exists${NC}"
else
    echo -e "  WireGuard config: ${RED}✗ Missing${NC}"
    config_ok=false
fi

# Check IP forwarding config
if [ -f "/etc/sysctl.d/99-wireguard.conf" ]; then
    echo -e "  IP forwarding config: ${GREEN}✓ Exists${NC}"
else
    echo -e "  IP forwarding config: ${RED}✗ Missing${NC}"
    config_ok=false
fi

# 3. Check firewall
print_status "Checking firewall..."

if ufw status | grep -q "Status: active"; then
    echo -e "  UFW Firewall: ${GREEN}✓ Active${NC}"
    if ufw status | grep -q "51820"; then
        echo -e "  WireGuard Port: ${GREEN}✓ Allowed${NC}"
    else
        echo -e "  WireGuard Port: ${RED}✗ Not allowed${NC}"
        config_ok=false
    fi
else
    echo -e "  UFW Firewall: ${RED}✗ Not active${NC}"
    config_ok=false
fi

# 4. Check IP forwarding
print_status "Checking IP forwarding..."

if [ "$(cat /proc/sys/net/ipv4/ip_forward)" = "1" ]; then
    echo -e "  IP Forwarding: ${GREEN}✓ Enabled${NC}"
else
    echo -e "  IP Forwarding: ${RED}✗ Not enabled${NC}"
    config_ok=false
fi

# 5. Test service start
print_status "Testing service start..."

# Stop services first
systemctl stop wireguard-mikrotik.service 2>/dev/null || true
wg-quick down wg0 2>/dev/null || true

# Start services
if systemctl start wireguard-mikrotik.service; then
    echo -e "  Service start: ${GREEN}✓ Success${NC}"
else
    echo -e "  Service start: ${RED}✗ Failed${NC}"
    services_ok=false
fi

# Check if WireGuard is running
sleep 2
if wg show wg0 >/dev/null 2>&1; then
    echo -e "  WireGuard interface: ${GREEN}✓ Running${NC}"
else
    echo -e "  WireGuard interface: ${RED}✗ Not running${NC}"
    services_ok=false
fi

# 6. Summary
echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="

if [ "$services_ok" = true ] && [ "$config_ok" = true ]; then
    print_success "✅ All systems ready for reboot!"
    echo ""
    print_status "Your VPS will automatically start:"
    echo "  ✓ WireGuard VPN service"
    echo "  ✓ IP forwarding"
    echo "  ✓ Firewall rules"
    echo "  ✓ Management scripts"
    echo ""
    print_status "After reboot, you can check status with:"
    echo "  wg-boot-status"
    echo "  wg-status"
    echo "  wg-mikrotik list"
    echo ""
    print_warning "Ready to reboot? Run: sudo reboot"
else
    print_error "❌ Some issues found that need fixing"
    echo ""
    if [ "$services_ok" = false ]; then
        print_warning "Service issues detected. Run:"
        echo "  sudo bash /opt/wireguard-mikrotik-vps/configure-boot-services.sh"
    fi
    if [ "$config_ok" = false ]; then
        print_warning "Configuration issues detected. Run:"
        echo "  sudo bash /opt/wireguard-mikrotik-vps/quick-fix.sh"
    fi
fi
