"""
WireGuard MikroTik Integration Service
Integrates with existing Django project for managing WireGuard VPN connections
"""

import os
import sys
import json
import subprocess
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing models and services
try:
    from routers.models import Router, RouterLog
    from routers.services.mikrotik_api import MikroTikAPIService
except ImportError:
    print("Warning: Could not import Django models. Make sure to run from Django project directory.")
    Router = None
    RouterLog = None
    MikroTikAPIService = None

logger = logging.getLogger(__name__)

class WireGuardMikroTikService:
    """
    Service for managing WireGuard VPN connections with MikroTik routers
    Integrates with existing Django billing system
    """
    
    def __init__(self):
        self.wg_config = "/etc/wireguard/wg0.conf"
        self.wg_interface = "wg0"
        self.management_script = "/usr/local/bin/wg-mikrotik"
        self.vpn_network = "10.10.0.0/24"
        self.vpn_gateway = "10.10.0.1"
        
    def add_router_to_wireguard(self, router: 'Router', public_key: str, 
                              ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """
        Add a MikroTik router to WireGuard VPN
        
        Args:
            router: Router model instance
            public_key: Router's WireGuard public key
            ip_address: Optional specific IP address for the router
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get next available IP if not specified
            if not ip_address:
                ip_address = self._get_next_available_ip()
                if not ip_address:
                    return False, "No available IP addresses in VPN range"
            
            # Validate IP address
            if not self._is_valid_vpn_ip(ip_address):
                return False, f"Invalid VPN IP address: {ip_address}"
            
            # Use management script to add router
            cmd = [self.management_script, "add", router.name, public_key, ip_address]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Update router model with VPN information
            router.vpn_ip = ip_address
            router.vpn_type = "wireguard"
            router.is_vpn_connected = True
            router.save()
            
            # Log the action
            self._log_router_action(router, "WIREGUARD_ADD", 
                                  f"Router added to WireGuard VPN with IP {ip_address}")
            
            return True, f"Router '{router.name}' added to WireGuard with IP {ip_address}"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to add router to WireGuard: {e.stderr}"
            logger.error(f"Router {router.name}: {error_msg}")
            self._log_router_action(router, "WIREGUARD_ERROR", error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error adding router: {str(e)}"
            logger.error(f"Router {router.name}: {error_msg}")
            self._log_router_action(router, "WIREGUARD_ERROR", error_msg)
            return False, error_msg
    
    def remove_router_from_wireguard(self, router: 'Router') -> Tuple[bool, str]:
        """
        Remove a MikroTik router from WireGuard VPN
        
        Args:
            router: Router model instance
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Use management script to remove router
            result = subprocess.run(
                [self.management_script, "remove", router.name],
                capture_output=True, text=True, check=True
            )
            
            # Update router model
            router.is_vpn_connected = False
            router.vpn_ip = None
            router.save()
            
            # Log the action
            self._log_router_action(router, "WIREGUARD_REMOVE", 
                                  "Router removed from WireGuard VPN")
            
            return True, f"Router '{router.name}' removed from WireGuard"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to remove router from WireGuard: {e.stderr}"
            logger.error(f"Router {router.name}: {error_msg}")
            self._log_router_action(router, "WIREGUARD_ERROR", error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error removing router: {str(e)}"
            logger.error(f"Router {router.name}: {error_msg}")
            self._log_router_action(router, "WIREGUARD_ERROR", error_msg)
            return False, error_msg
    
    def get_router_vpn_status(self, router: 'Router') -> Dict:
        """
        Get VPN connection status for a router
        
        Args:
            router: Router model instance
            
        Returns:
            Dictionary with status information
        """
        try:
            if not router.vpn_ip:
                return {
                    "is_connected": False,
                    "status": "not_configured",
                    "message": "Router not configured for VPN"
                }
            
            # Ping the router
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", router.vpn_ip],
                capture_output=True, text=True
            )
            
            is_online = result.returncode == 0
            
            # Test API connection if online
            api_accessible = False
            if is_online:
                try:
                    with MikroTikAPIService(router) as api:
                        api_accessible = True
                except Exception:
                    api_accessible = False
            
            return {
                "is_connected": is_online,
                "api_accessible": api_accessible,
                "status": "online" if is_online else "offline",
                "vpn_ip": router.vpn_ip,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking router status for {router.name}: {e}")
            return {
                "is_connected": False,
                "status": "error",
                "message": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def get_all_vpn_status(self) -> Dict:
        """
        Get VPN status for all routers
        
        Returns:
            Dictionary with status of all routers
        """
        if not Router:
            return {"error": "Router model not available"}
        
        routers = Router.objects.filter(vpn_type="wireguard")
        status = {
            "total_routers": routers.count(),
            "online_routers": 0,
            "offline_routers": 0,
            "routers": []
        }
        
        for router in routers:
            router_status = self.get_router_vpn_status(router)
            status["routers"].append({
                "id": router.id,
                "name": router.name,
                "vpn_ip": router.vpn_ip,
                "status": router_status
            })
            
            if router_status["is_connected"]:
                status["online_routers"] += 1
            else:
                status["offline_routers"] += 1
        
        return status
    
    def sync_router_with_wireguard(self, router: 'Router') -> Tuple[bool, str]:
        """
        Sync router configuration with WireGuard
        This ensures the router is properly configured for VPN access
        
        Args:
            router: Router model instance
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not router.vpn_ip:
                return False, "Router not configured for VPN"
            
            # Check if router is in WireGuard config
            with open(self.wg_config, 'r') as f:
                config_content = f.read()
            
            if router.name not in config_content:
                return False, "Router not found in WireGuard configuration"
            
            # Test connection to router
            status = self.get_router_vpn_status(router)
            if not status["is_connected"]:
                return False, f"Router is not reachable via VPN: {status.get('message', 'Unknown error')}"
            
            # Test API access
            if not status["api_accessible"]:
                return False, "Router API is not accessible via VPN"
            
            # Update router status
            router.is_vpn_connected = True
            router.last_vpn_check = datetime.now()
            router.save()
            
            self._log_router_action(router, "WIREGUARD_SYNC", 
                                  "Router successfully synced with WireGuard")
            
            return True, f"Router '{router.name}' synced successfully with WireGuard"
            
        except Exception as e:
            error_msg = f"Error syncing router with WireGuard: {str(e)}"
            logger.error(f"Router {router.name}: {error_msg}")
            self._log_router_action(router, "WIREGUARD_ERROR", error_msg)
            return False, error_msg
    
    def generate_router_config(self, router: 'Router', vps_public_key: str) -> str:
        """
        Generate MikroTik configuration for a router
        
        Args:
            router: Router model instance
            vps_public_key: VPS WireGuard public key
            
        Returns:
            Configuration string for MikroTik
        """
        if not router.vpn_ip:
            raise ValueError("Router must have a VPN IP assigned")
        
        # Get VPS IP from settings or environment
        vps_ip = getattr(settings, 'VPS_PUBLIC_IP', os.environ.get('VPS_PUBLIC_IP', 'YOUR_VPS_IP'))
        
        config = f"""# MikroTik WireGuard VPN Configuration Script
# Router: {router.name}
# VPN IP: {router.vpn_ip}
# 
# BEFORE IMPORTING:
# 1. Replace YOUR_VPS_IP with your actual VPS public IP: {vps_ip}
# 2. Replace VPS_PUBLIC_KEY with your VPS WireGuard public key: {vps_public_key}
# 3. After running, copy the router's public key to VPS config
# 4. Upload this file to MikroTik Files
# 5. Run: /import file={router.name}-wireguard.rsc

:log info "=========================================="
:log info "Starting WireGuard VPN Configuration"
:log info "Router: {router.name}"
:log info "VPN IP: {router.vpn_ip}"
:log info "=========================================="

# Set router identity
/system identity set name="{router.name}-Billing"

# Remove existing WireGuard interfaces
:log info "Removing old WireGuard interfaces..."
:foreach i in=[/interface wireguard find] do={{
    /interface wireguard remove $i
}}

# Create WireGuard interface
:log info "Creating WireGuard interface..."
/interface wireguard add \\
    name=wg-vpn \\
    listen-port=51820 \\
    comment="VPN to Billing Server"

# Get and display the public key (IMPORTANT: Save this!)
:delay 2s
:local wgpubkey [/interface wireguard get [find name=wg-vpn] public-key]
:log info "Router WireGuard Public Key: $wgpubkey"
:put "=========================================="
:put "⚠️  IMPORTANT: Copy this Public Key!"
:put "=========================================="
:put $wgpubkey
:put "=========================================="
:put "Add this key to your VPS using:"
:put "wg-mikrotik add {router.name} $wgpubkey {router.vpn_ip}"
:put "=========================================="

# Add peer (VPS server)
:log info "Adding WireGuard peer (VPS)..."
/interface wireguard peers add \\
    interface=wg-vpn \\
    public-key="{vps_public_key}" \\
    endpoint-address={vps_ip} \\
    endpoint-port=51820 \\
    allowed-address=0.0.0.0/0 \\
    persistent-keepalive=25s \\
    comment="VPS Server"

# Assign IP address
:log info "Assigning VPN IP address..."
/ip address add address={router.vpn_ip}/24 interface=wg-vpn

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
:if ($pingresult > 0) do={{
    :log info "✅ VPN Connected Successfully!"
    :put "=========================================="
    :put "✅ Configuration Complete!"
    :put "VPN Status: CONNECTED"
    :put "VPN IP: {router.vpn_ip}"
    :put "Gateway: 10.10.0.1"
    :put "API Port: 8728"
    :put "=========================================="
    :put "✅ Ping to VPS successful ($pingresult/3)"
    :put "=========================================="
}} else={{
    :log warning "⚠️  Cannot ping VPS yet"
    :put "=========================================="
    :put "⚠️  Configuration applied, but cannot ping VPS"
    :put "Make sure you:"
    :put "  1. Added router's public key to VPS"
    :put "  2. Restarted WireGuard on VPS"
    :put "  3. VPS firewall allows port 51820/udp"
    :put "=========================================="
}}

:put ""
:put "Router Public Key (add to VPS):"
:put $wgpubkey

:log info "Configuration script completed"
"""
        
        return config
    
    def _get_next_available_ip(self) -> Optional[str]:
        """Get the next available IP address in the VPN range"""
        try:
            # Read current config to find used IPs
            used_ips = set()
            if os.path.exists(self.wg_config):
                with open(self.wg_config, 'r') as f:
                    for line in f:
                        if 'AllowedIPs' in line:
                            # Extract IP from line like "AllowedIPs = 10.10.0.2/32"
                            ip = line.split('=')[1].strip().split('/')[0]
                            used_ips.add(ip)
            
            # Find next available IP
            for i in range(2, 255):  # 10.10.0.2 to 10.10.0.254
                ip = f"10.10.0.{i}"
                if ip not in used_ips:
                    return ip
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next available IP: {e}")
            return None
    
    def _is_valid_vpn_ip(self, ip_address: str) -> bool:
        """Validate if IP address is in the VPN range"""
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            
            # Check if it's in 10.10.0.x range
            if parts[0] == '10' and parts[1] == '10' and parts[2] == '0':
                ip_num = int(parts[3])
                return 2 <= ip_num <= 254
            
            return False
        except (ValueError, IndexError):
            return False
    
    def _log_router_action(self, router: 'Router', action: str, message: str):
        """Log router action if RouterLog model is available"""
        if RouterLog:
            try:
                RouterLog.objects.create(
                    router=router,
                    log_type="INFO",
                    action=action,
                    message=message,
                    details={"service": "wireguard_mikrotik"}
                )
            except Exception as e:
                logger.error(f"Failed to create router log: {e}")


# Django management command integration
class WireGuardManagementCommand:
    """Django management command for WireGuard operations"""
    
    def __init__(self):
        self.service = WireGuardMikroTikService()
    
    def add_router(self, router_name: str, public_key: str, ip_address: Optional[str] = None):
        """Add a router to WireGuard"""
        if not Router:
            print("Error: Router model not available")
            return
        
        try:
            router = Router.objects.get(name=router_name)
            success, message = self.service.add_router_to_wireguard(router, public_key, ip_address)
            print(f"{'Success' if success else 'Error'}: {message}")
        except Router.DoesNotExist:
            print(f"Error: Router '{router_name}' not found")
        except Exception as e:
            print(f"Error: {e}")
    
    def remove_router(self, router_name: str):
        """Remove a router from WireGuard"""
        if not Router:
            print("Error: Router model not available")
            return
        
        try:
            router = Router.objects.get(name=router_name)
            success, message = self.service.remove_router_from_wireguard(router)
            print(f"{'Success' if success else 'Error'}: {message}")
        except Router.DoesNotExist:
            print(f"Error: Router '{router_name}' not found")
        except Exception as e:
            print(f"Error: {e}")
    
    def list_routers(self):
        """List all WireGuard routers"""
        status = self.service.get_all_vpn_status()
        print(json.dumps(status, indent=2))
    
    def sync_router(self, router_name: str):
        """Sync a router with WireGuard"""
        if not Router:
            print("Error: Router model not available")
            return
        
        try:
            router = Router.objects.get(name=router_name)
            success, message = self.service.sync_router_with_wireguard(router)
            print(f"{'Success' if success else 'Error'}: {message}")
        except Router.DoesNotExist:
            print(f"Error: Router '{router_name}' not found")
        except Exception as e:
            print(f"Error: {e}")
    
    def generate_config(self, router_name: str, vps_public_key: str):
        """Generate configuration for a router"""
        if not Router:
            print("Error: Router model not available")
            return
        
        try:
            router = Router.objects.get(name=router_name)
            config = self.service.generate_router_config(router, vps_public_key)
            print(config)
        except Router.DoesNotExist:
            print(f"Error: Router '{router_name}' not found")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Command line interface
    import argparse
    
    parser = argparse.ArgumentParser(description="WireGuard MikroTik Management")
    parser.add_argument("command", choices=["add", "remove", "list", "sync", "generate"])
    parser.add_argument("--router", help="Router name")
    parser.add_argument("--public-key", help="Router public key")
    parser.add_argument("--ip", help="Router IP address")
    parser.add_argument("--vps-key", help="VPS public key for config generation")
    
    args = parser.parse_args()
    
    cmd = WireGuardManagementCommand()
    
    if args.command == "add":
        if not args.router or not args.public_key:
            print("Error: --router and --public-key are required for add command")
            sys.exit(1)
        cmd.add_router(args.router, args.public_key, args.ip)
    elif args.command == "remove":
        if not args.router:
            print("Error: --router is required for remove command")
            sys.exit(1)
        cmd.remove_router(args.router)
    elif args.command == "list":
        cmd.list_routers()
    elif args.command == "sync":
        if not args.router:
            print("Error: --router is required for sync command")
            sys.exit(1)
        cmd.sync_router(args.router)
    elif args.command == "generate":
        if not args.router or not args.vps_key:
            print("Error: --router and --vps-key are required for generate command")
            sys.exit(1)
        cmd.generate_config(args.router, args.vps_key)
