#!/bin/bash

# Check WireGuard MikroTik VPS Services Status
# This script checks which services are enabled for auto-start

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

print_status "Checking WireGuard MikroTik VPS Services Status..."

echo "=========================================="
echo "SERVICE STATUS CHECK"
echo "=========================================="

# Check WireGuard services
echo -e "\n${BLUE}WireGuard Services:${NC}"
echo "-------------------"

# Check wg-quick@wg0 service
if systemctl is-enabled wg-quick@wg0 >/dev/null 2>&1; then
    echo -e "wg-quick@wg0: ${GREEN}✓ Enabled${NC}"
else
    echo -e "wg-quick@wg0: ${RED}✗ Not enabled${NC}"
fi

# Check wireguard-manual service
if systemctl is-enabled wireguard-manual >/dev/null 2>&1; then
    echo -e "wireguard-manual: ${GREEN}✓ Enabled${NC}"
else
    echo -e "wireguard-manual: ${RED}✗ Not enabled${NC}"
fi

# Check if WireGuard is currently running
if wg show wg0 >/dev/null 2>&1; then
    echo -e "WireGuard Interface: ${GREEN}✓ Running${NC}"
else
    echo -e "WireGuard Interface: ${RED}✗ Not running${NC}"
fi

# Check management scripts
echo -e "\n${BLUE}Management Scripts:${NC}"
echo "-------------------"

if [ -f "/usr/local/bin/wg-mikrotik" ]; then
    echo -e "wg-mikrotik: ${GREEN}✓ Installed${NC}"
else
    echo -e "wg-mikrotik: ${RED}✗ Not installed${NC}"
fi

if [ -f "/usr/local/bin/wg-status" ]; then
    echo -e "wg-status: ${GREEN}✓ Installed${NC}"
else
    echo -e "wg-status: ${RED}✗ Not installed${NC}"
fi

if [ -f "/usr/local/bin/wg-test" ]; then
    echo -e "wg-test: ${GREEN}✓ Installed${NC}"
else
    echo -e "wg-test: ${RED}✗ Not installed${NC}"
fi

# Check firewall
echo -e "\n${BLUE}Firewall:${NC}"
echo "--------"
if ufw status | grep -q "Status: active"; then
    echo -e "UFW Firewall: ${GREEN}✓ Active${NC}"
    if ufw status | grep -q "51820"; then
        echo -e "WireGuard Port: ${GREEN}✓ Allowed${NC}"
    else
        echo -e "WireGuard Port: ${RED}✗ Not allowed${NC}"
    fi
else
    echo -e "UFW Firewall: ${RED}✗ Not active${NC}"
fi

# Check IP forwarding
echo -e "\n${BLUE}Network Configuration:${NC}"
echo "----------------------"
if [ "$(cat /proc/sys/net/ipv4/ip_forward)" = "1" ]; then
    echo -e "IP Forwarding: ${GREEN}✓ Enabled${NC}"
else
    echo -e "IP Forwarding: ${RED}✗ Not enabled${NC}"
fi

# Check if services will start on boot
echo -e "\n${BLUE}Boot Configuration:${NC}"
echo "-------------------"

# Check if WireGuard config exists
if [ -f "/etc/wireguard/wg0.conf" ]; then
    echo -e "WireGuard Config: ${GREEN}✓ Exists${NC}"
else
    echo -e "WireGuard Config: ${RED}✗ Missing${NC}"
fi

# Check if systemd services are enabled
echo -e "\n${BLUE}Systemd Services:${NC}"
echo "-----------------"
systemctl list-unit-files | grep -E "(wg-quick|wireguard)" | while read line; do
    service=$(echo $line | awk '{print $1}')
    status=$(echo $line | awk '{print $2}')
    if [ "$status" = "enabled" ]; then
        echo -e "$service: ${GREEN}✓ Enabled${NC}"
    else
        echo -e "$service: ${YELLOW}○ Available${NC}"
    fi
done

echo -e "\n${BLUE}Recommendations:${NC}"
echo "---------------"

# Check if manual service is enabled
if systemctl is-enabled wireguard-manual >/dev/null 2>&1; then
    echo -e "${GREEN}✓ WireGuard will start automatically on boot${NC}"
else
    echo -e "${YELLOW}⚠ Consider enabling wireguard-manual service for auto-start${NC}"
    echo "  Run: sudo systemctl enable wireguard-manual"
fi

# Check if firewall is persistent
if ufw status | grep -q "Status: active"; then
    echo -e "${GREEN}✓ Firewall will start automatically on boot${NC}"
else
    echo -e "${YELLOW}⚠ Consider enabling firewall for auto-start${NC}"
    echo "  Run: sudo ufw enable"
fi

echo -e "\n${BLUE}Summary:${NC}"
echo "--------"
if systemctl is-enabled wireguard-manual >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    echo -e "${GREEN}✅ All services are configured to start automatically on boot${NC}"
else
    echo -e "${YELLOW}⚠ Some services may not start automatically on boot${NC}"
    echo "  Run the fix script to ensure everything is configured properly"
fi
