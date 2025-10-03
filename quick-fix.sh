#!/bin/bash

# WireGuard MikroTik VPS Quick Fix Script
# This script fixes common installation issues

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

print_status "Starting WireGuard MikroTik VPS Quick Fix..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# 1. Clean up existing WireGuard
print_status "Cleaning up existing WireGuard..."
sudo systemctl stop wg-quick@wg0 2>/dev/null || true
sudo wg-quick down wg0 2>/dev/null || true
sudo ip link delete wg0 2>/dev/null || true
sudo pkill -f wg-quick 2>/dev/null || true
sleep 2

# 2. Start WireGuard manually
print_status "Starting WireGuard manually..."
sudo wg-quick up wg0

# 3. Create management scripts
print_status "Creating management scripts..."
sudo tee /usr/local/bin/wg-mikrotik > /dev/null << 'EOF'
#!/bin/bash
# WireGuard MikroTik Management Script
WG_CONFIG="/etc/wireguard/wg0.conf"
WG_NETWORK="10.10.0.0/24"
WG_SERVER_IP="10.10.0.1"

get_next_ip() {
    local used_ips=()
    local config_file="$WG_CONFIG"
    
    if [ -f "$config_file" ]; then
        while IFS= read -r line; do
            if [[ $line == AllowedIPs* ]]; then
                ip=$(echo "$line" | grep -o '10\.10\.0\.[0-9]\+')
                if [ ! -z "$ip" ]; then
                    used_ips+=("$ip")
                fi
            fi
        done < "$config_file"
    fi
    
    for i in {2..254}; do
        ip="10.10.0.$i"
        if [[ ! " ${used_ips[@]} " =~ " ${ip} " ]]; then
            echo "$ip"
            return
        fi
    done
    
    echo "No available IP addresses"
    return 1
}

add_router() {
    local router_name="$1"
    local public_key="$2"
    local ip_address="$3"
    
    if [ -z "$router_name" ] || [ -z "$public_key" ]; then
        echo "Usage: $0 add <router_name> <public_key> [ip_address]"
        exit 1
    fi
    
    if [ -z "$ip_address" ]; then
        ip_address=$(get_next_ip)
        if [ $? -ne 0 ]; then
            echo "Error: $ip_address"
            exit 1
        fi
    fi
    
    cat >> "$WG_CONFIG" << EOF2

# $router_name
[Peer]
PublicKey = $public_key
AllowedIPs = $ip_address/32
EOF2
    
    wg-quick down wg0 2>/dev/null || true
    wg-quick up wg0
    
    echo "Router '$router_name' added with IP: $ip_address"
}

remove_router() {
    local router_name="$1"
    
    if [ -z "$router_name" ]; then
        echo "Usage: $0 remove <router_name>"
        exit 1
    fi
    
    local temp_config=$(mktemp)
    local in_peer_section=false
    local skip_section=false
    
    while IFS= read -r line; do
        if [[ $line == "# $router_name" ]]; then
            skip_section=true
            continue
        elif [[ $line == "[Peer]" && $skip_section == true ]]; then
            skip_section=false
            continue
        elif [[ $line == "[Peer]" ]]; then
            in_peer_section=true
        elif [[ $line == "["* && $line != "[Peer]" ]]; then
            in_peer_section=false
        fi
        
        if [ "$skip_section" != true ]; then
            echo "$line" >> "$temp_config"
        fi
    done < "$WG_CONFIG"
    
    mv "$temp_config" "$WG_CONFIG"
    
    wg-quick down wg0 2>/dev/null || true
    wg-quick up wg0
    
    echo "Router '$router_name' removed"
}

list_routers() {
    echo "Connected WireGuard Peers:"
    echo "=========================="
    wg show wg0 peers | while read -r line; do
        if [[ $line == *"allowed ips"* ]]; then
            ip=$(echo "$line" | grep -o '10\.10\.0\.[0-9]\+')
            echo "  Router IP: $ip"
        fi
    done
}

restart_wg() {
    wg-quick down wg0 2>/dev/null || true
    wg-quick up wg0
    echo "WireGuard restarted"
}

case "$1" in
    add)
        add_router "$2" "$3" "$4"
        ;;
    remove)
        remove_router "$2"
        ;;
    list)
        list_routers
        ;;
    restart)
        restart_wg
        ;;
    *)
        echo "WireGuard MikroTik Management Script"
        echo "Usage: $0 {add|remove|list|restart}"
        echo ""
        echo "Commands:"
        echo "  add <router_name> <public_key> [ip_address]  - Add a new router"
        echo "  remove <router_name>                         - Remove a router"
        echo "  list                                        - List all routers"
        echo "  restart                                     - Restart WireGuard"
        exit 1
        ;;
esac
EOF

sudo tee /usr/local/bin/wg-status > /dev/null << 'EOF'
#!/bin/bash
echo "=========================================="
echo "WireGuard MikroTik Status"
echo "=========================================="
echo "WireGuard Service Status:"
systemctl is-active wg-quick@wg0 2>/dev/null || echo "manual"
echo ""
echo "WireGuard Interface Status:"
wg show wg0
echo ""
echo "Connected Peers:"
wg show wg0 peers
echo ""
echo "Network Configuration:"
ip addr show wg0 2>/dev/null || echo "WireGuard interface not found"
echo ""
echo "Firewall Status:"
ufw status | grep -E "(51820|WireGuard)"
echo ""
echo "=========================================="
echo "Management Commands:"
echo "  wg-mikrotik list          - List all routers"
echo "  wg-mikrotik add <name> <key> [ip] - Add router"
echo "  wg-mikrotik remove <name> - Remove router"
echo "  wg-mikrotik restart       - Restart WireGuard"
echo "=========================================="
EOF

sudo tee /usr/local/bin/wg-test > /dev/null << 'EOF'
#!/bin/bash
cd /opt/wireguard-mikrotik-vps
sudo python3 tools/test-wireguard-setup.py
EOF

# Make scripts executable
sudo chmod +x /usr/local/bin/wg-mikrotik
sudo chmod +x /usr/local/bin/wg-status
sudo chmod +x /usr/local/bin/wg-test

# 4. Create API service
print_status "Creating API service..."
sudo mkdir -p /opt/wireguard-mikrotik
sudo tee /opt/wireguard-mikrotik/wireguard_api.py > /dev/null << 'EOF'
#!/usr/bin/env python3
"""
WireGuard API Service for MikroTik Integration
"""

import json
import subprocess
import sys
from typing import Dict, List, Optional

class WireGuardAPI:
    def __init__(self):
        self.config_file = "/etc/wireguard/wg0.conf"
    
    def get_peers(self) -> List[Dict]:
        """Get list of WireGuard peers"""
        try:
            result = subprocess.run(['wg', 'show', 'wg0', 'peers'], 
                                  capture_output=True, text=True)
            peers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    peers.append({'public_key': line.strip()})
            return peers
        except Exception as e:
            return []
    
    def add_peer(self, public_key: str, allowed_ips: str) -> bool:
        """Add a new peer to WireGuard"""
        try:
            subprocess.run(['wg', 'set', 'wg0', 'peer', public_key, 
                          'allowed-ips', allowed_ips], check=True)
            return True
        except Exception as e:
            return False
    
    def remove_peer(self, public_key: str) -> bool:
        """Remove a peer from WireGuard"""
        try:
            subprocess.run(['wg', 'set', 'wg0', 'peer', public_key, 
                          'remove'], check=True)
            return True
        except Exception as e:
            return False

if __name__ == "__main__":
    api = WireGuardAPI()
    print(json.dumps(api.get_peers()))
EOF

sudo chmod +x /opt/wireguard-mikrotik/wireguard_api.py

# 5. Create manual service
print_status "Creating reliable WireGuard service..."
sudo tee /etc/systemd/system/wireguard-manual.service > /dev/null << 'EOF'
[Unit]
Description=WireGuard Manual Management
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'wg-quick down wg0 2>/dev/null || true; wg-quick up wg0'
ExecStop=/bin/bash -c 'wg-quick down wg0'
ExecReload=/bin/bash -c 'wg-quick down wg0; wg-quick up wg0'

[Install]
WantedBy=multi-user.target
EOF

# Enable the manual service
sudo systemctl daemon-reload
sudo systemctl enable wireguard-manual
sudo systemctl start wireguard-manual

# 6. Test everything
print_status "Testing the system..."
wg-test

print_success "Quick fix completed successfully!"
print_status "Your WireGuard MikroTik VPS is now fully operational!"
print_status "Use 'wg-status' to check status, 'wg-mikrotik list' to manage routers"
