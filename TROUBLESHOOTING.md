# WireGuard MikroTik VPS Troubleshooting Guide

## 🚨 Common Issues and Solutions

### 1. WireGuard Service Fails to Start

**Problem:** `systemctl start wg-quick@wg0` fails with "wg-quick: `wg0' already exists"

**Solution:**
```bash
# Stop and clean up
sudo systemctl stop wg-quick@wg0
sudo wg-quick down wg0 2>/dev/null || true
sudo ip link delete wg0 2>/dev/null || true
sudo pkill -f wg-quick 2>/dev/null || true
sleep 2

# Start manually
sudo wg-quick up wg0

# Use manual service instead
sudo systemctl enable wireguard-manual
sudo systemctl start wireguard-manual
```

### 2. Management Scripts Not Found

**Problem:** `wg-mikrotik: command not found`

**Solution:**
```bash
# Create management scripts
sudo tee /usr/local/bin/wg-mikrotik > /dev/null << 'EOF'
#!/bin/bash
# [Script content from install.sh]
EOF

sudo chmod +x /usr/local/bin/wg-mikrotik
```

### 3. Python Import Errors

**Problem:** `local variable 'subprocess' referenced before assignment`

**Solution:**
```bash
# Update the test script
cd /opt/wireguard-mikrotik-vps
sudo python3 -c "
import subprocess
import sys
print('Python imports working')
"
```

### 4. API Service Not Found

**Problem:** `python3: can't open file '/opt/wireguard-mikrotik/wireguard_api.py'`

**Solution:**
```bash
# Create API service
sudo mkdir -p /opt/wireguard-mikrotik
sudo tee /opt/wireguard-mikrotik/wireguard_api.py > /dev/null << 'EOF'
#!/usr/bin/env python3
# [API content from install.sh]
EOF

sudo chmod +x /opt/wireguard-mikrotik/wireguard_api.py
```

### 5. Firewall Issues

**Problem:** WireGuard port not accessible

**Solution:**
```bash
# Check firewall status
sudo ufw status

# Allow WireGuard port
sudo ufw allow 51820/udp
sudo ufw reload
```

### 6. IP Forwarding Not Enabled

**Problem:** VPN clients can't access internet

**Solution:**
```bash
# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 🔧 Prevention Strategies

### 1. Use the Updated Install Script

The updated `install.sh` now includes:
- Automatic cleanup of existing interfaces
- Management script creation
- API service setup
- Manual service configuration
- Error handling

### 2. Pre-Installation Checks

Before running the installer, check:
```bash
# Check if WireGuard is already installed
wg --version

# Check for existing interfaces
ip link show | grep wg

# Check system resources
free -h
df -h
```

### 3. Post-Installation Verification

After installation, always run:
```bash
# Test the system
wg-test

# Check status
wg-status

# Verify management tools
wg-mikrotik list
```

### 4. Backup Configuration

Before making changes:
```bash
# Backup WireGuard config
sudo cp /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.backup

# Backup keys
sudo cp -r /etc/wireguard/keys /etc/wireguard/keys.backup
```

## 🛠️ Manual Recovery

If the installation fails completely:

```bash
# 1. Clean up everything
sudo systemctl stop wg-quick@wg0 wireguard-manual 2>/dev/null || true
sudo wg-quick down wg0 2>/dev/null || true
sudo ip link delete wg0 2>/dev/null || true
sudo pkill -f wg-quick 2>/dev/null || true

# 2. Remove WireGuard
sudo apt remove --purge wireguard -y

# 3. Clean up configs
sudo rm -rf /etc/wireguard
sudo rm -f /usr/local/bin/wg-*

# 4. Reinstall
curl -sSL https://raw.githubusercontent.com/mmkash-web/wireguard/main/install.sh | bash
```

## 📋 Quick Fix Commands

```bash
# Fix all common issues
sudo systemctl stop wg-quick@wg0 2>/dev/null || true
sudo wg-quick down wg0 2>/dev/null || true
sudo ip link delete wg0 2>/dev/null || true
sudo pkill -f wg-quick 2>/dev/null || true
sleep 2
sudo wg-quick up wg0
sudo systemctl enable wireguard-manual
sudo systemctl start wireguard-manual

# Test everything
wg-test
```

## 🎯 Best Practices

1. **Always use the updated installer** - It handles all common issues
2. **Test after installation** - Run `wg-test` to verify everything works
3. **Use manual service** - More reliable than systemd wg-quick service
4. **Backup before changes** - Always backup configs before modifications
5. **Monitor logs** - Check `journalctl -u wireguard-manual` for issues

## 📞 Support

If you encounter issues not covered here:
1. Check the logs: `journalctl -u wireguard-manual`
2. Run diagnostics: `wg-test`
3. Check system status: `wg-status`
4. Verify network: `ping 10.10.0.1`
