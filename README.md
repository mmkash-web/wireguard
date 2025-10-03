# WireGuard MikroTik VPS Project

A complete WireGuard VPN solution for managing multiple MikroTik routers with a user-friendly interface.

## 🚀 Quick Start

### Option 1: One-Command Installation (Recommended)
```bash
# Install everything directly from GitHub
curl -sSL https://raw.githubusercontent.com/mmkash-web/wireguard/main/install.sh | bash
```

### Option 2: Manual Installation
```bash
# 1. Clone the repository
git clone https://github.com/mmkash-web/wireguard.git
cd wireguard

# 2. Run VPS installation
sudo bash scripts/install-wireguard-vps.sh

# 3. Generate router configs
./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_PUBLIC_KEY -c 10

# 4. Launch management interface
sudo python3 menu/wireguard-menu.py
```

### Option 3: Automated Deployment
```bash
# Deploy to VPS with one command
wget https://raw.githubusercontent.com/mmkash-web/wireguard/main/deploy.sh
chmod +x deploy.sh
./deploy.sh -v YOUR_VPS_IP -u root
```

## 📁 Project Structure

```
wireguard-mikrotik-vps/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── setup.sh                           # Quick setup script
├── scripts/                           # Installation and setup scripts
│   ├── install-wireguard-vps.sh      # VPS WireGuard installation
│   └── mikrotik-wireguard-setup.sh   # Router config generator
├── menu/                              # User interface files
│   ├── wireguard-menu.py             # Main management menu
│   ├── wireguard-dashboard.py        # Real-time dashboard
│   ├── launch-wireguard.bat          # Windows launcher
│   └── wireguard-menu.bat            # Windows menu launcher
├── tools/                             # Management and testing tools
│   ├── wireguard_mikrotik_service.py # Django integration service
│   ├── test-wireguard-setup.py       # System testing suite
│   └── validate-mikrotik-connection.py # Router validation
├── configs/                           # Configuration templates
│   └── (generated router configs)
└── docs/                              # Documentation
    ├── WIREGUARD_MIKROTIK_SETUP.md   # Complete setup guide
    └── MENU_SYSTEM_README.md         # Menu system documentation
```

## 🎯 Features

- **🔧 Complete VPS Setup** - Automated WireGuard installation
- **📊 Real-time Monitoring** - Live dashboard with auto-refresh
- **🔌 Router Management** - Add/remove/sync multiple routers
- **🧪 Testing Suite** - Comprehensive validation tools
- **📱 User-friendly Interface** - Intuitive menu system
- **🛡️ Security** - Firewall rules and secure key management
- **📈 Performance Monitoring** - System resource tracking

## 🛠️ Installation

### Prerequisites
- Ubuntu 20.04+ or Debian 10+
- Root access to VPS
- Python 3.7+
- MikroTik RouterOS 7.0+

### Step 1: Upload Project
```bash
# Upload this entire project folder to your VPS
scp -r wireguard-mikrotik-vps/ root@your-vps-ip:/opt/
```

### Step 2: Install Dependencies
```bash
# On VPS
cd /opt/wireguard-mikrotik-vps
sudo apt update && sudo apt install python3-pip -y
pip3 install -r requirements.txt
```

### Step 3: Run Installation
```bash
# Install WireGuard and setup VPS
sudo bash scripts/install-wireguard-vps.sh
```

### Step 4: Generate Router Configs
```bash
# Generate configurations for your routers
./scripts/mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_PUBLIC_KEY -c 10
```

## 🎮 Usage

### Management Menu
```bash
sudo python3 menu/wireguard-menu.py
```

### Real-time Dashboard
```bash
sudo python3 menu/wireguard-dashboard.py
```

### System Testing
```bash
sudo python3 tools/test-wireguard-setup.py
```

### Router Validation
```bash
python3 tools/validate-mikrotik-connection.py --router-ip 10.10.0.2
```

## 📊 Monitoring

The system provides comprehensive monitoring:

- **System Status** - CPU, memory, disk usage
- **WireGuard Status** - Service and interface status
- **Router Status** - Online/offline status for all routers
- **Network Monitoring** - Bandwidth and connection quality
- **Performance Metrics** - Real-time performance tracking

## 🔧 Management

### Adding Routers
1. Configure router with generated `.rsc` file
2. Get router's public key from output
3. Add to VPS: `wg-mikrotik add router1 <public_key> 10.10.0.2`

### Removing Routers
```bash
wg-mikrotik remove router1
```

### Checking Status
```bash
wg-status
wg-mikrotik list
```

## 🛡️ Security

- **Encrypted VPN Tunnels** - WireGuard encryption
- **Firewall Protection** - UFW rules for security
- **Secure Key Management** - Proper file permissions
- **API Access Control** - Restricted to VPN network only

## 📚 Documentation

- **Complete Setup Guide** - `docs/WIREGUARD_MIKROTIK_SETUP.md`
- **Menu System Guide** - `docs/MENU_SYSTEM_README.md`
- **API Documentation** - Built-in help system

## 🆘 Support

### Troubleshooting
```bash
# Check system status
sudo python3 tools/test-wireguard-setup.py

# View logs
journalctl -u wg-quick@wg0 -f

# Check WireGuard status
wg show wg0
```

### Common Commands
```bash
# Restart WireGuard
wg-mikrotik restart

# List all routers
wg-mikrotik list

# Test specific router
python3 tools/validate-mikrotik-connection.py --router-ip 10.10.0.2
```

## 🎯 Deployment Checklist

- [ ] VPS with Ubuntu 20.04+ or Debian 10+
- [ ] Root access to VPS
- [ ] Project uploaded to `/opt/wireguard-mikrotik-vps/`
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] WireGuard installed (`sudo bash scripts/install-wireguard-vps.sh`)
- [ ] Router configs generated
- [ ] Routers configured with `.rsc` files
- [ ] Routers added to VPS
- [ ] Management interface tested
- [ ] Monitoring dashboard working

## 📈 Scaling

This solution supports:
- **Up to 250 routers** (10.10.0.2-10.10.0.254)
- **High performance** with optimized WireGuard
- **Easy management** through user interface
- **Monitoring** and alerting capabilities

---

**Your WireGuard MikroTik VPS solution is ready for deployment!** 🎉

This project provides everything you need to manage multiple MikroTik routers through a secure WireGuard VPN with a comprehensive user interface.
