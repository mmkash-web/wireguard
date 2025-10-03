# WireGuard MikroTik Menu System

A comprehensive, user-friendly menu system for managing WireGuard VPN with multiple MikroTik routers.

## 🎯 Features

### 📊 **Real-time Monitoring**
- **Live Dashboard** - Real-time status of all routers
- **System Health** - CPU, memory, and service monitoring
- **Network Status** - WireGuard interface and peer monitoring
- **Auto-refresh** - Configurable refresh rates (1-60 seconds)

### 🔌 **Router Management**
- **Add/Remove Routers** - Easy router management
- **Status Monitoring** - Online/offline status tracking
- **API Testing** - Test MikroTik API connectivity
- **Sync Operations** - Sync routers with WireGuard
- **Bulk Operations** - Manage multiple routers at once

### 🛠️ **System Control**
- **Service Management** - Start/stop WireGuard services
- **Configuration** - View and edit configurations
- **Firewall Status** - Monitor firewall rules
- **Logs & Alerts** - View system and application logs
- **Performance** - Monitor system performance

### 🧪 **Testing & Validation**
- **System Tests** - Comprehensive system validation
- **Connection Tests** - Test individual router connections
- **Health Checks** - Automated health monitoring
- **Diagnostics** - Troubleshooting tools

## 🚀 Quick Start

### Windows Users:
```batch
# Double-click or run:
launch-wireguard.bat
```

### Linux/Mac Users:
```bash
# Run the main menu:
sudo python3 wireguard-menu.py

# Or run the dashboard:
sudo python3 wireguard-dashboard.py
```

## 📁 File Structure

```
wireguard-management/
├── wireguard-menu.py              # Main management menu
├── wireguard-dashboard.py         # Real-time dashboard
├── wireguard-menu.bat             # Windows launcher
├── launch-wireguard.bat           # Windows main launcher
├── test-wireguard-setup.py        # System testing
├── validate-mikrotik-connection.py # Router validation
├── wireguard_mikrotik_service.py  # Django integration
├── install-wireguard-vps.sh       # VPS installation
├── mikrotik-wireguard-setup.sh    # Config generator
└── MENU_SYSTEM_README.md          # This file
```

## 🎮 Menu System Overview

### 1. **Main Management Menu** (`wireguard-menu.py`)

**Features:**
- 📊 System Status & Health Check
- 🔌 Router Management
- 🌐 Network Monitoring
- ⚙️ Configuration Management
- 🔧 Tools & Utilities
- 📈 Performance Monitor
- 🛡️ Security & Logs
- 📚 Help & Documentation

**Usage:**
```bash
sudo python3 wireguard-menu.py
```

### 2. **Real-time Dashboard** (`wireguard-dashboard.py`)

**Features:**
- 🔄 Auto-refreshing display
- 📊 System overview
- 🔌 Router status table
- 📡 WireGuard peer details
- ⚡ Quick actions
- ⚙️ Configurable refresh rate

**Usage:**
```bash
sudo python3 wireguard-dashboard.py --refresh 5
```

### 3. **Windows Launcher** (`launch-wireguard.bat`)

**Features:**
- 🎯 One-click access to all tools
- 🔧 Management Menu
- 📊 Real-time Dashboard
- 🧪 System Testing
- 🔍 Router Testing
- 📋 Quick Status
- ⚙️ VPS Installation
- 🔧 Config Generator
- 📚 Documentation

## 🔧 Menu Functions

### System Status & Health Check
- ✅ WireGuard service status
- ✅ Interface status
- ✅ Firewall configuration
- ✅ System resources (CPU, memory)
- ✅ Connected peers count
- ✅ Uptime information

### Router Management
- 📋 **List All Routers** - Show all routers with status
- ➕ **Add New Router** - Add router with public key
- 🗑️ **Remove Router** - Remove router from WireGuard
- 🔄 **Sync Router** - Sync router with configuration
- 🔍 **Test Connection** - Test router connectivity
- 📊 **Status Details** - Detailed router information

### Network Monitoring
- 📊 **Real-time Status** - Live system status
- 🔄 **Continuous Monitoring** - Auto-refreshing display
- 📈 **Bandwidth Usage** - Network statistics
- 🚨 **Alert History** - System logs and alerts

### Tools & Utilities
- 🧪 **System Testing** - Comprehensive validation
- 🔍 **Connection Testing** - Individual router tests
- 📊 **Report Generation** - Status reports
- 🔧 **Diagnostics** - Troubleshooting tools

## 🎨 User Interface

### Color Coding
- 🟢 **Green** - Success, online, working
- 🔴 **Red** - Error, offline, failed
- 🟡 **Yellow** - Warning, caution
- 🔵 **Blue** - Information, details
- 🟣 **Purple** - Special actions
- ⚪ **White** - Normal text

### Status Indicators
- ✅ **Checkmark** - Success/Online
- ❌ **X Mark** - Error/Offline
- ⚠️ **Warning** - Caution/Attention
- 🔄 **Refresh** - Processing/Updating
- 📊 **Chart** - Statistics/Data
- 🔧 **Wrench** - Tools/Settings

## 🚀 Advanced Features

### Real-time Dashboard
```bash
# Start dashboard with custom refresh rate
sudo python3 wireguard-dashboard.py --refresh 10

# Dashboard features:
# - Auto-refreshing every 10 seconds
# - Live system status
# - Router status table
# - Quick action buttons
# - Keyboard shortcuts
```

### System Testing
```bash
# Run comprehensive system test
sudo python3 test-wireguard-setup.py

# Test specific router
python3 validate-mikrotik-connection.py --router-ip 10.10.0.2

# Test all routers
python3 validate-mikrotik-connection.py --all
```

### Configuration Management
```bash
# Generate router configs
./mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_KEY -c 10

# Install VPS setup
sudo bash install-wireguard-vps.sh
```

## 🔒 Security Features

### Access Control
- ✅ Root privileges required
- ✅ Secure key management
- ✅ Encrypted VPN tunnels
- ✅ Firewall protection

### Monitoring
- ✅ Connection logging
- ✅ Access tracking
- ✅ Error monitoring
- ✅ Performance alerts

## 📊 Monitoring Capabilities

### System Metrics
- CPU load and usage
- Memory consumption
- Disk space
- Network throughput
- Service status

### Router Metrics
- Connection status
- API accessibility
- Response times
- Error rates
- Uptime tracking

### Network Metrics
- WireGuard peer count
- Bandwidth usage
- Connection quality
- Latency monitoring
- Packet loss

## 🛠️ Troubleshooting

### Common Issues

#### Menu Won't Start
```bash
# Check Python installation
python3 --version

# Check root privileges
sudo whoami

# Check dependencies
pip3 install -r requirements.txt
```

#### Dashboard Not Updating
```bash
# Check WireGuard service
systemctl status wg-quick@wg0

# Check permissions
ls -la wireguard-*.py

# Run with debug
python3 wireguard-dashboard.py --refresh 1
```

#### Router Status Issues
```bash
# Test individual router
python3 validate-mikrotik-connection.py --router-ip 10.10.0.2

# Check WireGuard peers
wg show wg0

# Check system logs
journalctl -u wg-quick@wg0 -f
```

### Debug Mode
```bash
# Run with verbose output
python3 wireguard-menu.py --verbose

# Test system setup
python3 test-wireguard-setup.py --output debug.json
```

## 📚 Documentation

### Quick Reference
- **Main Menu**: `sudo python3 wireguard-menu.py`
- **Dashboard**: `sudo python3 wireguard-dashboard.py`
- **System Test**: `sudo python3 test-wireguard-setup.py`
- **Router Test**: `python3 validate-mikrotik-connection.py --router-ip IP`

### Configuration Files
- **WireGuard Config**: `/etc/wireguard/wg0.conf`
- **Management Script**: `/usr/local/bin/wg-mikrotik`
- **Status Script**: `/usr/local/bin/wg-status`
- **Logs**: `/var/log/wireguard-mikrotik.log`

### API Integration
- **Django Service**: `wireguard_mikrotik_service.py`
- **Management Commands**: `python3 manage.py wireguard`
- **API Endpoints**: `/api/wireguard/`

## 🎯 Best Practices

### Daily Operations
1. **Check Dashboard** - Monitor system status
2. **Review Logs** - Check for errors or alerts
3. **Test Connections** - Verify router connectivity
4. **Update Status** - Sync router information

### Weekly Maintenance
1. **System Test** - Run comprehensive validation
2. **Performance Review** - Check system metrics
3. **Security Audit** - Review access logs
4. **Backup Configs** - Save configuration files

### Monthly Tasks
1. **Key Rotation** - Update WireGuard keys
2. **Performance Analysis** - Review trends
3. **Security Updates** - Update system packages
4. **Documentation Review** - Update procedures

## 🆘 Support

### Getting Help
1. **Check Logs** - Review system and application logs
2. **Run Tests** - Use built-in testing tools
3. **Review Documentation** - Check setup guides
4. **System Status** - Use dashboard and menu tools

### Common Commands
```bash
# Quick status check
wg-status

# List all routers
wg-mikrotik list

# Test system
python3 test-wireguard-setup.py

# View logs
journalctl -u wg-quick@wg0 -f
```

---

**Your WireGuard MikroTik management system is now ready!** 🎉

This comprehensive menu system provides everything you need to manage your WireGuard VPN with multiple MikroTik routers through an intuitive, user-friendly interface.
