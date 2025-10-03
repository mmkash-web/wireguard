#!/bin/bash

# MikroTik WireGuard Configuration Generator
# This script generates configuration files for multiple MikroTik routers
# Each router gets a unique IP and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_IP=""
VPS_PUBLIC_KEY=""
ROUTER_COUNT=5
START_IP=2
CONFIG_DIR="mikrotik-wireguard-configs"

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

# Function to show usage
show_usage() {
    echo "MikroTik WireGuard Configuration Generator"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -v, --vps-ip IP          VPS public IP address (required)"
    echo "  -k, --vps-key KEY        VPS WireGuard public key (required)"
    echo "  -c, --count NUMBER       Number of routers to generate (default: 5)"
    echo "  -s, --start-ip NUMBER    Starting IP for routers (default: 2)"
    echo "  -d, --dir DIRECTORY      Output directory (default: mikrotik-wireguard-configs)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -v 203.0.113.1 -k abc123def456..."
    echo "  $0 --vps-ip 203.0.113.1 --vps-key abc123def456... --count 10"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--vps-ip)
            VPS_IP="$2"
            shift 2
            ;;
        -k|--vps-key)
            VPS_PUBLIC_KEY="$2"
            shift 2
            ;;
        -c|--count)
            ROUTER_COUNT="$2"
            shift 2
            ;;
        -s|--start-ip)
            START_IP="$2"
            shift 2
            ;;
        -d|--dir)
            CONFIG_DIR="$2"
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
if [ -z "$VPS_IP" ] || [ -z "$VPS_PUBLIC_KEY" ]; then
    print_error "VPS IP and VPS public key are required"
    show_usage
    exit 1
fi

# Validate router count
if ! [[ "$ROUTER_COUNT" =~ ^[0-9]+$ ]] || [ "$ROUTER_COUNT" -lt 1 ] || [ "$ROUTER_COUNT" -gt 250 ]; then
    print_error "Router count must be a number between 1 and 250"
    exit 1
fi

# Validate start IP
if ! [[ "$START_IP" =~ ^[0-9]+$ ]] || [ "$START_IP" -lt 2 ] || [ "$START_IP" -gt 254 ]; then
    print_error "Start IP must be a number between 2 and 254"
    exit 1
fi

# Check if start IP + router count exceeds 254
if [ $((START_IP + ROUTER_COUNT - 1)) -gt 254 ]; then
    print_error "Start IP ($START_IP) + router count ($ROUTER_COUNT) exceeds available IP range"
    exit 1
fi

print_status "Starting MikroTik WireGuard configuration generation..."
print_status "VPS IP: $VPS_IP"
print_status "VPS Public Key: $VPS_PUBLIC_KEY"
print_status "Router Count: $ROUTER_COUNT"
print_status "Starting IP: 10.10.0.$START_IP"
print_status "Output Directory: $CONFIG_DIR"

# Create output directory
mkdir -p "$CONFIG_DIR"

# Function to generate router configuration
generate_router_config() {
    local router_num=$1
    local router_ip=$2
    local config_file="$CONFIG_DIR/router${router_num}-wireguard.rsc"
    
    print_status "Generating configuration for Router $router_num (IP: 10.10.0.$router_ip)..."
    
    cat > "$config_file" << EOF
# MikroTik WireGuard VPN Configuration Script
# Router $router_num - Import this file to your MikroTik (RouterOS 7.0+)
# 
# BEFORE IMPORTING:
# 1. Replace YOUR_VPS_IP with your actual VPS public IP: $VPS_IP
# 2. Replace VPS_PUBLIC_KEY with your VPS WireGuard public key: $VPS_PUBLIC_KEY
# 3. After running, copy the router's public key to VPS config
# 4. Upload this file to MikroTik Files
# 5. Run: /import file=router${router_num}-wireguard.rsc

:log info "=========================================="
:log info "Starting WireGuard VPN Configuration"
:log info "Router: Router$router_num"
:log info "VPN IP: 10.10.0.$router_ip"
:log info "=========================================="

# Set router identity
/system identity set name="Router${router_num}-Billing"

# Remove existing WireGuard interfaces
:log info "Removing old WireGuard interfaces..."
:foreach i in=[/interface wireguard find] do={
    /interface wireguard remove \$i
}

# Create WireGuard interface
:log info "Creating WireGuard interface..."
/interface wireguard add \\
    name=wg-vpn \\
    listen-port=51820 \\
    comment="VPN to Billing Server"

# Get and display the public key (IMPORTANT: Save this!)
:delay 2s
:local wgpubkey [/interface wireguard get [find name=wg-vpn] public-key]
:log info "Router WireGuard Public Key: \$wgpubkey"
:put "=========================================="
:put "⚠️  IMPORTANT: Copy this Public Key!"
:put "=========================================="
:put \$wgpubkey
:put "=========================================="
:put "Add this key to your VPS using:"
:put "wg-mikrotik add router${router_num} \$wgpubkey 10.10.0.$router_ip"
:put "=========================================="

# Add peer (VPS server)
:log info "Adding WireGuard peer (VPS)..."
/interface wireguard peers add \\
    interface=wg-vpn \\
    public-key="$VPS_PUBLIC_KEY" \\
    endpoint-address=$VPS_IP \\
    endpoint-port=51820 \\
    allowed-address=0.0.0.0/0 \\
    persistent-keepalive=25s \\
    comment="VPS Server"

# Assign IP address
:log info "Assigning VPN IP address..."
/ip address add address=10.10.0.$router_ip/24 interface=wg-vpn

# Enable MikroTik API
:log info "Enabling API service..."
/ip service set api disabled=no port=8728

# Add firewall rule to allow API from VPN only
:log info "Configuring firewall..."
/ip firewall filter add \\
    chain=input \\
    protocol=tcp \\
    dst-port=8728 \\
    in-interface=wg-vpn \\
    action=accept \\
    comment="Allow API from VPN" \\
    place-before=0

/ip firewall filter add \\
    chain=input \\
    protocol=tcp \\
    dst-port=8728 \\
    action=drop \\
    comment="Block API from outside"

# Wait for connection
:log info "Waiting for VPN connection (10 seconds)..."
:delay 10s

# Test connection
:log info "Testing VPN connection..."
:local pingresult [/ping 10.10.0.1 count=3]
:if (\$pingresult > 0) do={
    :log info "✅ VPN Connected Successfully!"
    :put "=========================================="
    :put "✅ Configuration Complete!"
    :put "VPN Status: CONNECTED"
    :put "VPN IP: 10.10.0.$router_ip"
    :put "Gateway: 10.10.0.1"
    :put "API Port: 8728"
    :put "=========================================="
    :put "✅ Ping to VPS successful (\$pingresult/3)"
    :put "=========================================="
} else={
    :log warning "⚠️  Cannot ping VPS yet"
    :put "=========================================="
    :put "⚠️  Configuration applied, but cannot ping VPS"
    :put "Make sure you:"
    :put "  1. Added router's public key to VPS"
    :put "  2. Restarted WireGuard on VPS"
    :put "  3. VPS firewall allows port 51820/udp"
    :put "=========================================="
}

:put ""
:put "Router Public Key (add to VPS):"
:put \$wgpubkey

:log info "Configuration script completed"
EOF

    print_success "Generated configuration for Router $router_num"
}

# Generate configurations for all routers
for ((i=1; i<=ROUTER_COUNT; i++)); do
    router_ip=$((START_IP + i - 1))
    generate_router_config $i $router_ip
done

# Create a master configuration file
print_status "Creating master configuration file..."
cat > "$CONFIG_DIR/README.md" << EOF
# MikroTik WireGuard Configuration Files

This directory contains WireGuard configuration files for $ROUTER_COUNT MikroTik routers.

## Files Generated

EOF

for ((i=1; i<=ROUTER_COUNT; i++)); do
    router_ip=$((START_IP + i - 1))
    echo "- \`router${i}-wireguard.rsc\` - Router $i (IP: 10.10.0.$router_ip)" >> "$CONFIG_DIR/README.md"
done

cat >> "$CONFIG_DIR/README.md" << EOF

## Setup Instructions

### 1. VPS Setup
First, run the VPS installation script:
\`\`\`bash
sudo bash install-wireguard-vps.sh
\`\`\`

### 2. Router Configuration
For each router:

1. **Upload the configuration file** to your MikroTik router
2. **Edit the file** and replace:
   - \`YOUR_VPS_IP\` with your actual VPS IP: \`$VPS_IP\`
   - \`VPS_PUBLIC_KEY\` with your VPS public key: \`$VPS_PUBLIC_KEY\`
3. **Import the file** on MikroTik:
   \`\`\`bash
   /import file=router${i}-wireguard.rsc
   \`\`\`
4. **Copy the router's public key** from the output
5. **Add the router to VPS**:
   \`\`\`bash
   wg-mikrotik add router${i} <ROUTER_PUBLIC_KEY> 10.10.0.$router_ip
   \`\`\`

### 3. Verification
Check if everything is working:
\`\`\`bash
# On VPS
wg-status
wg-mikrotik list

# On MikroTik
/ping 10.10.0.1
/interface wireguard/print
\`\`\`

## Router Information

| Router | VPN IP | Config File | Status |
|--------|--------|-------------|--------|
EOF

for ((i=1; i<=ROUTER_COUNT; i++)); do
    router_ip=$((START_IP + i - 1))
    echo "| Router $i | 10.10.0.$router_ip | router${i}-wireguard.rsc | Pending |" >> "$CONFIG_DIR/README.md"
done

cat >> "$CONFIG_DIR/README.md" << EOF

## Management Commands

### On VPS:
\`\`\`bash
# Check status
wg-status

# List all routers
wg-mikrotik list

# Add a router
wg-mikrotik add <router_name> <public_key> [ip_address]

# Remove a router
wg-mikrotik remove <router_name>

# Restart WireGuard
wg-mikrotik restart
\`\`\`

### On MikroTik:
\`\`\`bash
# Check WireGuard status
/interface wireguard/print
/interface wireguard/peers/print

# Test VPN connection
/ping 10.10.0.1

# Check API status
/ip service/print where name=api
\`\`\`

## Troubleshooting

### Router can't connect to VPS:
1. Check VPS firewall: \`ufw status\`
2. Verify VPS WireGuard is running: \`systemctl status wg-quick@wg0\`
3. Check router's public key is added to VPS config
4. Verify VPS public key in router config

### API not accessible:
1. Check API is enabled: \`/ip service/print where name=api\`
2. Verify firewall rules allow API from VPN
3. Test from VPS: \`telnet 10.10.0.$router_ip 8728\`

### Performance issues:
1. Check WireGuard logs: \`journalctl -u wg-quick@wg0 -f\`
2. Monitor bandwidth: \`wg show\`
3. Check router resources: \`/system resource/print\`
EOF

# Create a batch setup script
print_status "Creating batch setup script..."
cat > "$CONFIG_DIR/setup-all-routers.sh" << EOF
#!/bin/bash

# Batch setup script for all MikroTik routers
# This script helps you add all routers to the VPS at once

set -e

VPS_IP="$VPS_IP"
VPS_PUBLIC_KEY="$VPS_PUBLIC_KEY"

echo "MikroTik WireGuard Batch Setup"
echo "=============================="
echo ""
echo "This script will help you add all $ROUTER_COUNT routers to your VPS."
echo "Make sure you have:"
echo "1. Configured all routers with the .rsc files"
echo "2. Collected all router public keys"
echo "3. VPS WireGuard server is running"
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "For each router, you'll need to:"
echo "1. Run the .rsc file on the router"
echo "2. Copy the router's public key"
echo "3. Add it to the VPS using the command shown"
echo ""

for ((i=1; i<=ROUTER_COUNT; i++)); do
    router_ip=$((START_IP + i - 1))
    echo "Router $i (IP: 10.10.0.$router_ip):"
    echo "1. Import router${i}-wireguard.rsc on MikroTik"
    echo "2. Copy the public key from the output"
    echo "3. Run this command on VPS:"
    echo "   wg-mikrotik add router${i} <ROUTER_PUBLIC_KEY> 10.10.0.$router_ip"
    echo ""
    read -p "Press Enter when Router $i is configured..."
done

echo ""
echo "All routers configured! Checking status..."
wg-mikrotik list
echo ""
echo "Setup complete!"
EOF

chmod +x "$CONFIG_DIR/setup-all-routers.sh"

# Create a quick test script
print_status "Creating test script..."
cat > "$CONFIG_DIR/test-connections.sh" << EOF
#!/bin/bash

# Test script to verify all router connections

echo "Testing WireGuard Connections"
echo "============================="
echo ""

# Check VPS WireGuard status
echo "VPS WireGuard Status:"
systemctl is-active wg-quick@wg0
echo ""

# Show connected peers
echo "Connected Peers:"
wg show wg0 peers
echo ""

# Test each router
for ((i=1; i<=ROUTER_COUNT; i++)); do
    router_ip=$((START_IP + i - 1))
    echo "Testing Router $i (10.10.0.$router_ip):"
    
    if ping -c 1 -W 3 10.10.0.$router_ip > /dev/null 2>&1; then
        echo "  ✅ Router $i is online"
        
        # Test API connection
        if timeout 3 bash -c "</dev/tcp/10.10.0.$router_ip/8728" 2>/dev/null; then
            echo "  ✅ API is accessible"
        else
            echo "  ❌ API is not accessible"
        fi
    else
        echo "  ❌ Router $i is offline"
    fi
    echo ""
done

echo "Test complete!"
EOF

chmod +x "$CONFIG_DIR/test-connections.sh"

# Display summary
print_success "Configuration generation completed!"
echo ""
echo "=========================================="
echo "Generated Files"
echo "=========================================="
echo "Output Directory: $CONFIG_DIR"
echo ""

for ((i=1; i<=ROUTER_COUNT; i++)); do
    router_ip=$((START_IP + i - 1))
    echo "Router $i:"
    echo "  Config: router${i}-wireguard.rsc"
    echo "  VPN IP: 10.10.0.$router_ip"
    echo ""
done

echo "Additional Files:"
echo "  README.md - Complete setup instructions"
echo "  setup-all-routers.sh - Batch setup script"
echo "  test-connections.sh - Connection test script"
echo ""

echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo "1. Run the VPS installation script:"
echo "   sudo bash install-wireguard-vps.sh"
echo ""
echo "2. Configure each router:"
echo "   - Upload and import the .rsc files"
echo "   - Replace VPS_IP and VPS_PUBLIC_KEY in each file"
echo "   - Copy each router's public key"
echo ""
echo "3. Add routers to VPS:"
echo "   wg-mikrotik add router1 <public_key> 10.10.0.$START_IP"
echo "   wg-mikrotik add router2 <public_key> 10.10.0.$((START_IP + 1))"
echo "   # ... and so on"
echo ""
echo "4. Test connections:"
echo "   cd $CONFIG_DIR && ./test-connections.sh"
echo ""

print_success "All configuration files generated successfully!"
