#!/bin/bash

# WireGuard MikroTik VPS Boot Services Configuration
# This script ensures all services start automatically on boot

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

print_status "Configuring WireGuard MikroTik VPS for automatic boot startup..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# 1. Ensure WireGuard configuration exists
print_status "Checking WireGuard configuration..."
if [ ! -f "/etc/wireguard/wg0.conf" ]; then
    print_error "WireGuard configuration not found at /etc/wireguard/wg0.conf"
    print_status "Please run the installation script first"
    exit 1
fi

# 2. Create reliable WireGuard service
print_status "Creating reliable WireGuard service..."
cat > /etc/systemd/system/wireguard-mikrotik.service << 'EOF'
[Unit]
Description=WireGuard MikroTik VPS Service
After=network-online.target
Wants=network-online.target
Requires=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/bin/bash -c 'wg-quick down wg0 2>/dev/null || true'
ExecStart=/bin/bash -c 'wg-quick up wg0'
ExecStop=/bin/bash -c 'wg-quick down wg0'
ExecReload=/bin/bash -c 'wg-quick down wg0; wg-quick up wg0'
TimeoutStartSec=30
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# 3. Enable the service
print_status "Enabling WireGuard service..."
systemctl daemon-reload
systemctl enable wireguard-mikrotik.service
systemctl start wireguard-mikrotik.service

# 4. Ensure IP forwarding is persistent
print_status "Configuring persistent IP forwarding..."
cat > /etc/sysctl.d/99-wireguard.conf << 'EOF'
# WireGuard MikroTik VPS IP Forwarding
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
EOF

# Apply immediately
sysctl -p /etc/sysctl.d/99-wireguard.conf

# 5. Ensure firewall rules are persistent
print_status "Configuring persistent firewall rules..."
ufw --force enable
ufw allow 51820/udp comment 'WireGuard'
ufw allow ssh comment 'SSH'

# 6. Create startup script for additional services
print_status "Creating startup script..."
cat > /usr/local/bin/wireguard-startup.sh << 'EOF'
#!/bin/bash
# WireGuard MikroTik VPS Startup Script

# Wait for network
sleep 5

# Ensure WireGuard is running
if ! wg show wg0 >/dev/null 2>&1; then
    echo "Starting WireGuard..."
    wg-quick up wg0
fi

# Log startup
echo "$(date): WireGuard MikroTik VPS started" >> /var/log/wireguard-mikrotik-startup.log
EOF

chmod +x /usr/local/bin/wireguard-startup.sh

# 7. Create systemd service for startup script
print_status "Creating startup service..."
cat > /etc/systemd/system/wireguard-startup.service << 'EOF'
[Unit]
Description=WireGuard MikroTik VPS Startup
After=wireguard-mikrotik.service
Wants=wireguard-mikrotik.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/wireguard-startup.sh
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wireguard-startup.service

# 8. Create log directory
print_status "Creating log directory..."
mkdir -p /var/log/wireguard-mikrotik
chmod 755 /var/log/wireguard-mikrotik

# 9. Test the configuration
print_status "Testing configuration..."
systemctl status wireguard-mikrotik.service --no-pager

# 10. Create monitoring script
print_status "Creating monitoring script..."
cat > /usr/local/bin/wireguard-monitor.sh << 'EOF'
#!/bin/bash
# WireGuard MikroTik VPS Monitor

LOG_FILE="/var/log/wireguard-mikrotik/monitor.log"

check_wireguard() {
    if wg show wg0 >/dev/null 2>&1; then
        echo "$(date): WireGuard is running" >> $LOG_FILE
        return 0
    else
        echo "$(date): WireGuard is not running, attempting restart..." >> $LOG_FILE
        wg-quick up wg0
        return 1
    fi
}

check_wireguard
EOF

chmod +x /usr/local/bin/wireguard-monitor.sh

# 11. Create cron job for monitoring
print_status "Setting up monitoring cron job..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/wireguard-monitor.sh") | crontab -

# 12. Create systemd timer for monitoring
print_status "Creating monitoring timer..."
cat > /etc/systemd/system/wireguard-monitor.service << 'EOF'
[Unit]
Description=WireGuard MikroTik VPS Monitor

[Service]
Type=oneshot
ExecStart=/usr/local/bin/wireguard-monitor.sh
EOF

cat > /etc/systemd/system/wireguard-monitor.timer << 'EOF'
[Unit]
Description=WireGuard MikroTik VPS Monitor Timer
Requires=wireguard-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable wireguard-monitor.timer
systemctl start wireguard-monitor.timer

# 13. Create status check script
print_status "Creating status check script..."
cat > /usr/local/bin/wg-boot-status << 'EOF'
#!/bin/bash
# WireGuard MikroTik VPS Boot Status Check

echo "=========================================="
echo "WireGuard MikroTik VPS Boot Status"
echo "=========================================="

echo "Services Status:"
echo "----------------"
systemctl is-active wireguard-mikrotik.service
systemctl is-enabled wireguard-mikrotik.service

echo ""
echo "WireGuard Interface:"
echo "-------------------"
wg show wg0 2>/dev/null || echo "Not running"

echo ""
echo "Network Configuration:"
echo "---------------------"
ip addr show wg0 2>/dev/null || echo "Interface not found"

echo ""
echo "Firewall Status:"
echo "---------------"
ufw status | grep -E "(51820|Status)"

echo ""
echo "IP Forwarding:"
echo "-------------"
cat /proc/sys/net/ipv4/ip_forward

echo ""
echo "Boot Services:"
echo "-------------"
systemctl list-unit-files | grep -E "(wireguard|wg-quick)" | grep enabled

echo ""
echo "Recent Logs:"
echo "-----------"
tail -5 /var/log/wireguard-mikrotik/monitor.log 2>/dev/null || echo "No logs yet"
EOF

chmod +x /usr/local/bin/wg-boot-status

# 14. Test everything
print_status "Testing all services..."
wg-boot-status

print_success "Boot services configuration completed!"
print_status "Services configured for auto-start:"
echo "  ✓ WireGuard MikroTik Service"
echo "  ✓ IP Forwarding (persistent)"
echo "  ✓ Firewall Rules (persistent)"
echo "  ✓ Startup Script"
echo "  ✓ Monitoring Timer"
echo "  ✓ Status Check Script"

print_status "To check status anytime, run: wg-boot-status"
print_status "To test reboot, run: sudo reboot"

echo ""
print_warning "IMPORTANT: After reboot, run 'wg-boot-status' to verify everything started correctly"
