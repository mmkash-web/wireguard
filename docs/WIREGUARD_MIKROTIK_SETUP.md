# WireGuard MikroTik Integration Setup Guide

Complete guide for setting up WireGuard VPN with multiple MikroTik routers for your billing system.

## 📋 Overview

This setup provides:
- **Automated VPS installation** with WireGuard server
- **Multiple MikroTik router support** (up to 250 routers)
- **Django integration** with your existing billing system
- **API management** for adding/removing routers
- **Monitoring and status checking**
- **Automatic IP assignment** and configuration

## 🚀 Quick Start

### 1. VPS Setup (5 minutes)

```bash
# Download and run the VPS installation script
wget https://raw.githubusercontent.com/your-repo/mikrotikvpn/main/install-wireguard-vps.sh
chmod +x install-wireguard-vps.sh
sudo ./install-wireguard-vps.sh
```

**Save the VPS public key** - you'll need it for router configuration!

### 2. Generate Router Configurations (2 minutes)

```bash
# Generate configurations for 5 routers
chmod +x mikrotik-wireguard-setup.sh
./mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_PUBLIC_KEY -c 5
```

### 3. Configure Routers (10 minutes per router)

For each router:
1. Upload the generated `.rsc` file to MikroTik
2. Import the configuration: `/import file=router1-wireguard.rsc`
3. Copy the router's public key from the output
4. Add to VPS: `wg-mikrotik add router1 <ROUTER_PUBLIC_KEY>`

### 4. Verify Setup

```bash
# Check status
wg-status

# List all routers
wg-mikrotik list

# Test connections
cd mikrotik-wireguard-configs && ./test-connections.sh
```

---

## 📁 File Structure

```
mikrotikvpn/
├── install-wireguard-vps.sh          # VPS installation script
├── mikrotik-wireguard-setup.sh       # Router config generator
├── wireguard_mikrotik_service.py     # Django integration service
├── WIREGUARD_MIKROTIK_SETUP.md       # This documentation
└── mikrotik-wireguard-configs/       # Generated router configs
    ├── router1-wireguard.rsc
    ├── router2-wireguard.rsc
    ├── setup-all-routers.sh
    ├── test-connections.sh
    └── README.md
```

---

## 🔧 Detailed Setup Instructions

### Part 1: VPS Installation

The VPS installation script (`install-wireguard-vps.sh`) automatically:

1. **Installs WireGuard** and required packages
2. **Generates server keys** (private/public key pair)
3. **Configures WireGuard server** with proper firewall rules
4. **Creates management tools** for adding/removing routers
5. **Sets up Python API service** for Django integration
6. **Enables IP forwarding** and NAT rules

**Key outputs:**
- VPS Public Key (save this!)
- Server IP: `10.10.0.1`
- VPN Network: `10.10.0.0/24`
- Management commands: `wg-mikrotik`, `wg-status`

### Part 2: Router Configuration Generation

The router config generator (`mikrotik-wireguard-setup.sh`) creates:

1. **Individual `.rsc` files** for each router
2. **Batch setup script** for easy deployment
3. **Test scripts** for verification
4. **Documentation** with setup instructions

**Usage:**
```bash
./mikrotik-wireguard-setup.sh -v 203.0.113.1 -k abc123def456... -c 10
```

**Parameters:**
- `-v, --vps-ip`: VPS public IP address
- `-k, --vps-key`: VPS WireGuard public key
- `-c, --count`: Number of routers (default: 5)
- `-s, --start-ip`: Starting IP number (default: 2)
- `-d, --dir`: Output directory (default: mikrotik-wireguard-configs)

### Part 3: MikroTik Router Setup

Each router needs:

1. **RouterOS 7.0+** (WireGuard support required)
2. **Configuration file** uploaded and imported
3. **Public key** copied and added to VPS
4. **API enabled** for billing system access

**Step-by-step:**

1. **Upload config file** to MikroTik Files
2. **Edit the file** and replace:
   - `YOUR_VPS_IP` with actual VPS IP
   - `VPS_PUBLIC_KEY` with VPS public key
3. **Import configuration:**
   ```bash
   /import file=router1-wireguard.rsc
   ```
4. **Copy the router's public key** from output
5. **Add router to VPS:**
   ```bash
   wg-mikrotik add router1 <ROUTER_PUBLIC_KEY> 10.10.0.2
   ```

---

## 🐍 Django Integration

### Service Integration

The `wireguard_mikrotik_service.py` provides Django integration:

```python
from wireguard_mikrotik_service import WireGuardMikroTikService

# Initialize service
wg_service = WireGuardMikroTikService()

# Add router to WireGuard
success, message = wg_service.add_router_to_wireguard(
    router=router_instance,
    public_key="router_public_key",
    ip_address="10.10.0.2"  # Optional
)

# Check router status
status = wg_service.get_router_vpn_status(router_instance)

# Get all VPN status
all_status = wg_service.get_all_vpn_status()

# Generate router config
config = wg_service.generate_router_config(
    router=router_instance,
    vps_public_key="vps_public_key"
)
```

### Management Commands

Add to your Django management commands:

```python
# management/commands/wireguard.py
from django.core.management.base import BaseCommand
from wireguard_mikrotik_service import WireGuardManagementCommand

class Command(BaseCommand):
    help = 'Manage WireGuard MikroTik connections'
    
    def add_arguments(self, parser):
        parser.add_argument('action', choices=['add', 'remove', 'list', 'sync'])
        parser.add_argument('--router', help='Router name')
        parser.add_argument('--public-key', help='Router public key')
        parser.add_argument('--ip', help='Router IP address')
    
    def handle(self, *args, **options):
        cmd = WireGuardManagementCommand()
        # Implementation based on action
```

### API Endpoints

Add to your Django URLs:

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/wireguard/status/', views.wireguard_status, name='wireguard_status'),
    path('api/wireguard/add-router/', views.add_router, name='add_router'),
    path('api/wireguard/remove-router/', views.remove_router, name='remove_router'),
]
```

---

## 🔍 Monitoring and Management

### Status Checking

```bash
# Check WireGuard service status
wg-status

# List all connected routers
wg-mikrotik list

# Test specific router
ping 10.10.0.2
telnet 10.10.0.2 8728
```

### Management Commands

```bash
# Add a new router
wg-mikrotik add router5 abc123def456... 10.10.0.5

# Remove a router
wg-mikrotik remove router5

# Restart WireGuard
wg-mikrotik restart

# Check logs
journalctl -u wg-quick@wg0 -f
tail -f /var/log/wireguard-mikrotik.log
```

### Python API

```python
# Check router status
status = wg_service.get_router_vpn_status(router)
print(f"Router {router.name}: {status['status']}")

# Get all routers status
all_status = wg_service.get_all_vpn_status()
print(f"Online: {all_status['online_routers']}/{all_status['total_routers']}")

# Sync router with WireGuard
success, message = wg_service.sync_router_with_wireguard(router)
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Router Can't Connect to VPS

**Symptoms:**
- Router shows "Cannot ping VPS" message
- WireGuard interface is down

**Solutions:**
```bash
# Check VPS firewall
sudo ufw status
sudo ufw allow 51820/udp

# Check WireGuard service
sudo systemctl status wg-quick@wg0
sudo journalctl -u wg-quick@wg0 -f

# Verify router's public key is in VPS config
sudo wg show wg0
```

#### 2. API Not Accessible

**Symptoms:**
- Router is online but API connection fails
- Django can't connect to router

**Solutions:**
```bash
# Check API service on MikroTik
/ip service/print where name=api

# Test API from VPS
telnet 10.10.0.2 8728

# Check firewall rules on MikroTik
/ip firewall filter/print where comment~"API"
```

#### 3. IP Address Conflicts

**Symptoms:**
- Multiple routers with same IP
- Connection drops randomly

**Solutions:**
```bash
# Check used IPs
grep "AllowedIPs" /etc/wireguard/wg0.conf

# Reassign IP
wg-mikrotik remove router1
wg-mikrotik add router1 <key> 10.10.0.10
```

#### 4. Performance Issues

**Symptoms:**
- Slow API responses
- High latency

**Solutions:**
```bash
# Check WireGuard statistics
sudo wg show wg0

# Monitor bandwidth
iftop -i wg0

# Check router resources
/interface wireguard/print
/system resource/print
```

### Debug Commands

```bash
# VPS debugging
sudo wg show wg0                    # Show WireGuard status
sudo journalctl -u wg-quick@wg0 -f  # Watch logs
sudo ufw status verbose             # Check firewall
ip route show                       # Check routing

# MikroTik debugging
/interface wireguard/print          # Show WireGuard config
/interface wireguard/peers/print    # Show peers
/log/print where topics~"wireguard" # Show WireGuard logs
/ping 10.10.0.1 count=5            # Test VPS connectivity
```

---

## 📊 Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VPS Server                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              WireGuard Server                   │   │
│  │  IP: 10.10.0.1/24                             │   │
│  │  Port: 51820/UDP                              │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Django Billing App                │   │
│  │  - Router Management                           │   │
│  │  - API Integration                            │   │
│  │  - Status Monitoring                          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │ WireGuard VPN Tunnels
        ┌─────────────┼─────────────┬─────────────┐
        │             │             │             │
┌───────▼──────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐
│   Router 1   │ │ Router 2 │ │ Router 3 │ │ Router N │
│ 10.10.0.2    │ │10.10.0.3 │ │10.10.0.4 │ │10.10.0.N │
│ Nairobi      │ │ Mombasa  │ │ Kisumu   │ │ Location │
│ MikroTik     │ │ MikroTik │ │ MikroTik │ │ MikroTik │
└──────────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## 🔒 Security Considerations

### Firewall Rules

**VPS Firewall:**
```bash
# Allow WireGuard
sudo ufw allow 51820/udp

# Allow SSH
sudo ufw allow 22/tcp

# Block other ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

**MikroTik Firewall:**
```bash
# Allow API only from VPN
/ip firewall filter add chain=input protocol=tcp dst-port=8728 in-interface=wg-vpn action=accept
/ip firewall filter add chain=input protocol=tcp dst-port=8728 action=drop
```

### Key Management

1. **Store keys securely** - Use proper file permissions
2. **Rotate keys regularly** - Generate new keys periodically
3. **Backup configurations** - Keep copies of working configs
4. **Monitor access** - Log all API connections

### Network Security

1. **Use strong keys** - Generate 256-bit keys
2. **Limit API access** - Only allow from VPN network
3. **Monitor traffic** - Watch for unusual patterns
4. **Regular updates** - Keep WireGuard and MikroTik updated

---

## 📈 Scaling and Performance

### Adding More Routers

```bash
# Generate configs for more routers
./mikrotik-wireguard-setup.sh -v YOUR_VPS_IP -k YOUR_VPS_KEY -c 50

# Add routers individually
wg-mikrotik add router51 <key> 10.10.0.51
```

### Performance Optimization

1. **Bandwidth monitoring:**
   ```bash
   # Monitor WireGuard traffic
   sudo wg show wg0
   iftop -i wg0
   ```

2. **Resource management:**
   ```bash
   # Check system resources
   htop
   free -h
   df -h
   ```

3. **Connection pooling:**
   - Use persistent connections in Django
   - Implement connection timeouts
   - Monitor API response times

### High Availability

1. **Backup VPS:**
   - Keep configuration backups
   - Document recovery procedures
   - Test failover scenarios

2. **Router redundancy:**
   - Multiple routers per location
   - Automatic failover
   - Health monitoring

---

## 📚 API Reference

### WireGuardMikroTikService

#### Methods

**`add_router_to_wireguard(router, public_key, ip_address=None)`**
- Adds a router to WireGuard VPN
- Returns: `(success: bool, message: str)`

**`remove_router_from_wireguard(router)`**
- Removes a router from WireGuard VPN
- Returns: `(success: bool, message: str)`

**`get_router_vpn_status(router)`**
- Gets VPN status for a specific router
- Returns: `Dict` with status information

**`get_all_vpn_status()`**
- Gets VPN status for all routers
- Returns: `Dict` with all routers status

**`sync_router_with_wireguard(router)`**
- Syncs router configuration with WireGuard
- Returns: `(success: bool, message: str)`

**`generate_router_config(router, vps_public_key)`**
- Generates MikroTik configuration for router
- Returns: `str` configuration content

### Management Commands

**`wg-mikrotik add <name> <public_key> [ip]`**
- Add a router to WireGuard

**`wg-mikrotik remove <name>`**
- Remove a router from WireGuard

**`wg-mikrotik list`**
- List all connected routers

**`wg-mikrotik restart`**
- Restart WireGuard service

**`wg-status`**
- Show comprehensive status

---

## ✅ Success Checklist

### VPS Setup
- [ ] WireGuard installed and running
- [ ] Firewall configured correctly
- [ ] Management tools working
- [ ] Python API service running
- [ ] VPS public key saved

### Router Configuration
- [ ] All routers have unique IP addresses
- [ ] Router configurations imported successfully
- [ ] All routers can ping VPS (10.10.0.1)
- [ ] API accessible from VPS
- [ ] Firewall rules configured

### Django Integration
- [ ] Service integrated with existing models
- [ ] Management commands working
- [ ] API endpoints functional
- [ ] Status monitoring active
- [ ] Error handling implemented

### Testing
- [ ] All routers show as online
- [ ] API calls working from Django
- [ ] Status monitoring accurate
- [ ] Error recovery working
- [ ] Performance acceptable

---

## 🆘 Support and Maintenance

### Regular Maintenance

1. **Weekly:**
   - Check router status
   - Review logs for errors
   - Monitor performance

2. **Monthly:**
   - Update WireGuard if needed
   - Review security settings
   - Backup configurations

3. **Quarterly:**
   - Rotate keys
   - Test disaster recovery
   - Review scaling needs

### Getting Help

1. **Check logs:**
   ```bash
   sudo journalctl -u wg-quick@wg0 -f
   tail -f /var/log/wireguard-mikrotik.log
   ```

2. **Test connectivity:**
   ```bash
   wg-status
   ./test-connections.sh
   ```

3. **Verify configuration:**
   ```bash
   sudo wg show wg0
   cat /etc/wireguard/wg0.conf
   ```

---

**Your WireGuard MikroTik integration is now complete!** 🎉

This setup provides a robust, scalable solution for managing multiple MikroTik routers through a secure WireGuard VPN connection, fully integrated with your Django billing system.
