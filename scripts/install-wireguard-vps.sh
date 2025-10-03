#!/bin/bash

# WireGuard VPS Installation Script for MikroTik Integration
# This script sets up a WireGuard server that can handle multiple MikroTik routers
# Compatible with Ubuntu 20.04+ and Debian 10+

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WG_INTERFACE="wg0"
WG_PORT="51820"
WG_NETWORK="10.10.0.0/24"
WG_SERVER_IP="10.10.0.1"
WG_CONFIG_DIR="/etc/wireguard"
WG_KEYS_DIR="$WG_CONFIG_DIR/keys"

# Function to print colored output
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

print_status "Starting WireGuard VPS installation for MikroTik integration..."

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing WireGuard and required packages..."
apt install -y wireguard iptables-persistent ufw curl wget

# Enable IP forwarding
print_status "Enabling IP forwarding..."
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding=1' >> /etc/sysctl.conf
sysctl -p

# Create WireGuard directories
print_status "Creating WireGuard directories..."
mkdir -p "$WG_KEYS_DIR"
chmod 700 "$WG_KEYS_DIR"

# Generate server keys
print_status "Generating WireGuard server keys..."
cd "$WG_KEYS_DIR"

# Generate private key
wg genkey | tee server_private.key | wg pubkey > server_public.key
chmod 600 server_private.key

# Get server keys
SERVER_PRIVATE_KEY=$(cat server_private.key)
SERVER_PUBLIC_KEY=$(cat server_public.key)

print_success "Server keys generated:"
print_status "Private Key: $SERVER_PRIVATE_KEY"
print_status "Public Key: $SERVER_PUBLIC_KEY"

# Get network interface
print_status "Detecting network interface..."
NET_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
if [ -z "$NET_INTERFACE" ]; then
    print_error "Could not detect network interface"
    exit 1
fi
print_status "Using network interface: $NET_INTERFACE"

# Create WireGuard configuration
print_status "Creating WireGuard configuration..."
cat > "$WG_CONFIG_DIR/$WG_INTERFACE.conf" << EOF
[Interface]
Address = $WG_SERVER_IP/24
ListenPort = $WG_PORT
PrivateKey = $SERVER_PRIVATE_KEY

# Save and restore iptables rules
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o $NET_INTERFACE -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o $NET_INTERFACE -j MASQUERADE

# MikroTik Router Peers will be added here
# Each router gets an IP in the range 10.10.0.2-10.10.0.254
EOF

# Set proper permissions
chmod 600 "$WG_CONFIG_DIR/$WG_INTERFACE.conf"

# Configure firewall
print_status "Configuring firewall..."
ufw allow $WG_PORT/udp comment "WireGuard"
ufw allow 22/tcp comment "SSH"
ufw --force enable

# Start and enable WireGuard
print_status "Starting WireGuard service..."
systemctl enable wg-quick@$WG_INTERFACE
wg-quick up $WG_INTERFACE

# Create management script
print_status "Creating WireGuard management script..."
cat > /usr/local/bin/wg-mikrotik << 'EOF'
#!/bin/bash

# WireGuard MikroTik Management Script
# Usage: wg-mikrotik add <router_name> <public_key> [ip_address]
#        wg-mikrotik remove <router_name>
#        wg-mikrotik list
#        wg-mikrotik restart

WG_CONFIG="/etc/wireguard/wg0.conf"
WG_NETWORK="10.10.0.0/24"
WG_SERVER_IP="10.10.0.1"

# Function to get next available IP
get_next_ip() {
    local used_ips=()
    local config_file="$WG_CONFIG"
    
    # Extract used IPs from config
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
    
    # Find next available IP
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

# Function to add router
add_router() {
    local router_name="$1"
    local public_key="$2"
    local ip_address="$3"
    
    if [ -z "$router_name" ] || [ -z "$public_key" ]; then
        echo "Usage: $0 add <router_name> <public_key> [ip_address]"
        exit 1
    fi
    
    # Get IP address if not provided
    if [ -z "$ip_address" ]; then
        ip_address=$(get_next_ip)
        if [ $? -ne 0 ]; then
            echo "Error: $ip_address"
            exit 1
        fi
    fi
    
    # Add peer to config
    cat >> "$WG_CONFIG" << EOF

# $router_name
[Peer]
PublicKey = $public_key
AllowedIPs = $ip_address/32
EOF
    
    # Reload WireGuard
    wg-quick down wg0 2>/dev/null || true
    wg-quick up wg0
    
    echo "Router '$router_name' added with IP: $ip_address"
    echo "Router configuration:"
    echo "  Name: $router_name"
    echo "  VPN IP: $ip_address"
    echo "  Gateway: $WG_SERVER_IP"
    echo "  Port: 51820"
    echo "  Public Key: $public_key"
}

# Function to remove router
remove_router() {
    local router_name="$1"
    
    if [ -z "$router_name" ]; then
        echo "Usage: $0 remove <router_name>"
        exit 1
    fi
    
    # Create temporary config without the router
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
    
    # Replace original config
    mv "$temp_config" "$WG_CONFIG"
    
    # Reload WireGuard
    wg-quick down wg0 2>/dev/null || true
    wg-quick up wg0
    
    echo "Router '$router_name' removed"
}

# Function to list routers
list_routers() {
    echo "Connected WireGuard Peers:"
    echo "=========================="
    wg show wg0 peers | while read -r line; do
        if [[ $line == *"allowed ips"* ]]; then
            ip=$(echo "$line" | grep -o '10\.10\.0\.[0-9]\+')
            echo "  Router IP: $ip"
        fi
    done
    
    echo ""
    echo "Configuration file peers:"
    echo "========================"
    grep -A 3 "# " "$WG_CONFIG" | grep -E "(# |PublicKey|AllowedIPs)" | while read -r line; do
        if [[ $line == "# "* ]]; then
            echo "  Router: ${line#*# }"
        elif [[ $line == "PublicKey"* ]]; then
            echo "    Key: ${line#*PublicKey = }"
        elif [[ $line == "AllowedIPs"* ]]; then
            echo "    IP: ${line#*AllowedIPs = }"
            echo ""
        fi
    done
}

# Function to restart WireGuard
restart_wg() {
    wg-quick down wg0 2>/dev/null || true
    wg-quick up wg0
    echo "WireGuard restarted"
}

# Main script logic
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
        echo ""
        echo "Examples:"
        echo "  $0 add router1 abc123def456... 10.10.0.2"
        echo "  $0 add router2 xyz789uvw012..."
        echo "  $0 remove router1"
        echo "  $0 list"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/wg-mikrotik

# Create Python API service for MikroTik integration
print_status "Creating Python API service..."
mkdir -p /opt/wireguard-mikrotik
cat > /opt/wireguard-mikrotik/wireguard_api.py << 'EOF'
#!/usr/bin/env python3
"""
WireGuard MikroTik API Service
Manages WireGuard peers and MikroTik router connections
"""

import os
import sys
import json
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/wireguard-mikrotik.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WireGuardMikroTikAPI:
    """API service for managing WireGuard peers and MikroTik connections"""
    
    def __init__(self):
        self.wg_config = "/etc/wireguard/wg0.conf"
        self.wg_interface = "wg0"
        self.management_script = "/usr/local/bin/wg-mikrotik"
    
    def add_router(self, router_name: str, public_key: str, ip_address: Optional[str] = None) -> Dict:
        """Add a new MikroTik router to WireGuard"""
        try:
            # Use management script to add router
            cmd = [self.management_script, "add", router_name, public_key]
            if ip_address:
                cmd.append(ip_address)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "message": f"Router '{router_name}' added successfully",
                "output": result.stdout.strip()
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add router {router_name}: {e.stderr}")
            return {
                "success": False,
                "message": f"Failed to add router: {e.stderr}",
                "error": str(e)
            }
    
    def remove_router(self, router_name: str) -> Dict:
        """Remove a MikroTik router from WireGuard"""
        try:
            result = subprocess.run(
                [self.management_script, "remove", router_name],
                capture_output=True, text=True, check=True
            )
            
            return {
                "success": True,
                "message": f"Router '{router_name}' removed successfully",
                "output": result.stdout.strip()
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove router {router_name}: {e.stderr}")
            return {
                "success": False,
                "message": f"Failed to remove router: {e.stderr}",
                "error": str(e)
            }
    
    def list_routers(self) -> Dict:
        """List all connected WireGuard peers"""
        try:
            result = subprocess.run(
                [self.management_script, "list"],
                capture_output=True, text=True, check=True
            )
            
            return {
                "success": True,
                "routers": result.stdout.strip(),
                "output": result.stdout.strip()
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list routers: {e.stderr}")
            return {
                "success": False,
                "message": f"Failed to list routers: {e.stderr}",
                "error": str(e)
            }
    
    def get_router_status(self, router_ip: str) -> Dict:
        """Check if a specific router is connected"""
        try:
            # Ping the router
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", router_ip],
                capture_output=True, text=True
            )
            
            is_online = result.returncode == 0
            
            return {
                "success": True,
                "router_ip": router_ip,
                "is_online": is_online,
                "status": "online" if is_online else "offline"
            }
        except Exception as e:
            logger.error(f"Failed to check router status for {router_ip}: {e}")
            return {
                "success": False,
                "message": f"Failed to check router status: {e}",
                "error": str(e)
            }
    
    def restart_wireguard(self) -> Dict:
        """Restart WireGuard service"""
        try:
            result = subprocess.run(
                [self.management_script, "restart"],
                capture_output=True, text=True, check=True
            )
            
            return {
                "success": True,
                "message": "WireGuard restarted successfully",
                "output": result.stdout.strip()
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart WireGuard: {e.stderr}")
            return {
                "success": False,
                "message": f"Failed to restart WireGuard: {e.stderr}",
                "error": str(e)
            }

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python3 wireguard_api.py {add|remove|list|status|restart}")
        sys.exit(1)
    
    api = WireGuardMikroTikAPI()
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 4:
            print("Usage: python3 wireguard_api.py add <router_name> <public_key> [ip_address]")
            sys.exit(1)
        result = api.add_router(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif command == "remove":
        if len(sys.argv) < 3:
            print("Usage: python3 wireguard_api.py remove <router_name>")
            sys.exit(1)
        result = api.remove_router(sys.argv[2])
    elif command == "list":
        result = api.list_routers()
    elif command == "status":
        if len(sys.argv) < 3:
            print("Usage: python3 wireguard_api.py status <router_ip>")
            sys.exit(1)
        result = api.get_router_status(sys.argv[2])
    elif command == "restart":
        result = api.restart_wireguard()
    else:
        print("Unknown command. Use: add, remove, list, status, restart")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
EOF

chmod +x /opt/wireguard-mikrotik/wireguard_api.py

# Create systemd service for the API
print_status "Creating systemd service..."
cat > /etc/systemd/system/wireguard-mikrotik.service << EOF
[Unit]
Description=WireGuard MikroTik API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wireguard-mikrotik
ExecStart=/usr/bin/python3 /opt/wireguard-mikrotik/wireguard_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wireguard-mikrotik

# Create status check script
print_status "Creating status check script..."
cat > /usr/local/bin/wg-status << 'EOF'
#!/bin/bash

# WireGuard Status Check Script

echo "=========================================="
echo "WireGuard MikroTik Status"
echo "=========================================="

# Check WireGuard service
echo "WireGuard Service Status:"
systemctl is-active wg-quick@wg0

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

chmod +x /usr/local/bin/wg-status

# Final status check
print_status "Performing final status check..."
sleep 2

# Check if WireGuard is running
if systemctl is-active --quiet wg-quick@wg0; then
    print_success "WireGuard is running"
else
    print_error "WireGuard failed to start"
    exit 1
fi

# Display final information
echo ""
print_success "WireGuard VPS installation completed successfully!"
echo ""
echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
echo "WireGuard Interface: $WG_INTERFACE"
echo "WireGuard Port: $WG_PORT"
echo "VPN Network: $WG_NETWORK"
echo "Server IP: $WG_SERVER_IP"
echo "Config File: $WG_CONFIG_DIR/$WG_INTERFACE.conf"
echo ""
echo "Server Public Key:"
echo "$SERVER_PUBLIC_KEY"
echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo "1. Copy the server public key above"
echo "2. Use it in your MikroTik router configuration"
echo "3. Get the router's public key from MikroTik"
echo "4. Add the router using: wg-mikrotik add <name> <public_key>"
echo ""
echo "Management Commands:"
echo "  wg-status                 - Check status"
echo "  wg-mikrotik list          - List routers"
echo "  wg-mikrotik add <name> <key> [ip] - Add router"
echo "  wg-mikrotik remove <name> - Remove router"
echo "  wg-mikrotik restart       - Restart WireGuard"
echo ""
echo "Logs:"
echo "  journalctl -u wg-quick@wg0 -f"
echo "  tail -f /var/log/wireguard-mikrotik.log"
echo "=========================================="

print_success "Installation complete! Your VPS is ready for MikroTik routers."
