# WireGuard MikroTik VPS Deployment Guide

Complete deployment guide for the WireGuard MikroTik management system.

## 🚀 Quick Deployment from GitHub

### Option 1: One-Command VPS Setup

```bash
# Clone and setup everything in one command
curl -sSL https://raw.githubusercontent.com/mmkash-web/wireguard/main/setup.sh | bash
```

### Option 2: Manual GitHub Deployment

```bash
# 1. Clone the repository
git clone https://github.com/mmkash-web/wireguard.git
cd wireguard

# 2. Make scripts executable
chmod +x scripts/*.sh
chmod +x menu/*.py
chmod +x tools/*.py

# 3. Install dependencies
sudo apt update && sudo apt install python3-pip -y
pip3 install -r requirements.txt

# 4. Run VPS setup
sudo bash scripts/install-wireguard-vps.sh

# 5. Generate router configs
./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_PUBLIC_KEY -c 10
```

### Option 3: Automated Deployment Script

```bash
# Download and run deployment script
wget https://raw.githubusercontent.com/mmkash-web/wireguard/main/deploy.sh
chmod +x deploy.sh
./deploy.sh -v YOUR_VPS_IP -u root
```

## 📋 Prerequisites

- **VPS Requirements:**
  - Ubuntu 20.04+ or Debian 10+
  - Root access
  - At least 1GB RAM
  - 10GB free disk space

- **Router Requirements:**
  - MikroTik RouterOS 7.0+
  - WireGuard support
  - API access enabled

## 🔧 Step-by-Step Deployment

### Step 1: Prepare VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git curl wget python3 python3-pip
```

### Step 2: Clone Repository

```bash
# Clone the project
git clone https://github.com/mmkash-web/wireguard.git
cd wireguard

# Set proper permissions
sudo chown -R root:root .
chmod +x scripts/*.sh menu/*.py tools/*.py
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt
```

### Step 4: Install WireGuard

```bash
# Run the VPS installation script
sudo bash scripts/install-wireguard-vps.sh
```

**Save the VPS public key** - you'll need it for router configuration!

### Step 5: Generate Router Configurations

```bash
# Generate configs for your routers
./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_PUBLIC_KEY -c 10
```

### Step 6: Configure Routers

For each router:
1. Upload the generated `.rsc` file to MikroTik
2. Import: `/import file=router1-wireguard.rsc`
3. Copy the router's public key from output
4. Add to VPS: `wg-mikrotik add router1 <public_key> 10.10.0.2`

### Step 7: Start Management Interface

```bash
# Start the management menu
sudo python3 menu/wireguard-menu.py

# Or start the real-time dashboard
sudo python3 menu/wireguard-dashboard.py
```

## 🎯 GitHub Repository Features

The GitHub repository at [https://github.com/mmkash-web/wireguard.git](https://github.com/mmkash-web/wireguard.git) includes:

- **📁 Complete Project Structure** - All files organized properly
- **📄 Comprehensive Documentation** - Setup guides and API docs
- **🔧 Installation Scripts** - Automated VPS setup
- **🎮 User Interface** - Menu system and dashboard
- **🧪 Testing Tools** - Validation and monitoring
- **📦 Dependencies** - All required packages listed

## 🔄 Updates and Maintenance

### Updating from GitHub

```bash
# Navigate to project directory
cd /opt/wireguard-mikrotik-vps

# Pull latest changes
git pull origin main

# Update dependencies if needed
pip3 install -r requirements.txt

# Restart services if needed
sudo systemctl restart wg-quick@wg0
```

### Backup Configuration

```bash
# Backup WireGuard configuration
sudo cp /etc/wireguard/wg0.conf /opt/wireguard-mikrotik-vps/backup/

# Backup project directory
tar -czf wireguard-backup-$(date +%Y%m%d).tar.gz /opt/wireguard-mikrotik-vps/
```

## 🛠️ Management Commands

### Quick Access Commands

```bash
# Management menu
wg-menu

# Real-time dashboard
wg-dashboard

# System test
wg-test

# Check status
wg-status

# List routers
wg-mikrotik list
```

### Service Management

```bash
# Start WireGuard
sudo systemctl start wg-quick@wg0

# Stop WireGuard
sudo systemctl stop wg-quick@wg0

# Restart WireGuard
sudo systemctl restart wg-quick@wg0

# Check status
sudo systemctl status wg-quick@wg0
```

## 📊 Monitoring and Logs

### System Monitoring

```bash
# Real-time dashboard
sudo python3 menu/wireguard-dashboard.py

# System test
sudo python3 tools/test-wireguard-setup.py

# Router validation
python3 tools/validate-mikrotik-connection.py --router-ip 10.10.0.2
```

### Log Files

```bash
# WireGuard logs
journalctl -u wg-quick@wg0 -f

# System logs
tail -f /var/log/syslog

# Application logs
tail -f /var/log/wireguard-mikrotik.log
```

## 🚨 Troubleshooting

### Common Issues

#### 1. WireGuard Not Starting
```bash
# Check service status
sudo systemctl status wg-quick@wg0

# Check configuration
sudo wg show

# Check logs
journalctl -u wg-quick@wg0 -f
```

#### 2. Router Connection Issues
```bash
# Test router connectivity
python3 tools/validate-mikrotik-connection.py --router-ip 10.10.0.2

# Check WireGuard peers
sudo wg show wg0

# Test API access
telnet 10.10.0.2 8728
```

#### 3. Permission Issues
```bash
# Fix permissions
sudo chown -R root:root /opt/wireguard-mikrotik-vps
chmod +x /opt/wireguard-mikrotik-vps/scripts/*.sh
chmod +x /opt/wireguard-mikrotik-vps/menu/*.py
chmod +x /opt/wireguard-mikrotik-vps/tools/*.py
```

## 📈 Scaling and Performance

### Adding More Routers

```bash
# Generate more configs
./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_KEY -c 50

# Add routers individually
wg-mikrotik add router51 <public_key> 10.10.0.51
```

### Performance Optimization

```bash
# Monitor system resources
htop

# Check WireGuard performance
sudo wg show wg0

# Monitor network traffic
iftop -i wg0
```

## 🔒 Security Best Practices

### Firewall Configuration

```bash
# Check firewall status
sudo ufw status

# Allow WireGuard port
sudo ufw allow 51820/udp

# Allow SSH
sudo ufw allow 22/tcp
```

### Key Management

```bash
# Backup keys
sudo cp -r /etc/wireguard/keys/ /opt/wireguard-mikrotik-vps/backup/

# Rotate keys periodically
sudo wg genkey | sudo tee /etc/wireguard/keys/server_private_new.key
```

## 📚 Additional Resources

- **GitHub Repository:** [https://github.com/mmkash-web/wireguard.git](https://github.com/mmkash-web/wireguard.git)
- **Complete Setup Guide:** `docs/WIREGUARD_MIKROTIK_SETUP.md`
- **Menu System Guide:** `docs/MENU_SYSTEM_README.md`
- **WireGuard Documentation:** [https://www.wireguard.com/](https://www.wireguard.com/)
- **MikroTik Documentation:** [https://help.mikrotik.com/](https://help.mikrotik.com/)

---

**Your WireGuard MikroTik VPS solution is now easily deployable from GitHub!** 🎉

The repository provides everything needed for a complete, professional WireGuard management system with multiple MikroTik router support.
