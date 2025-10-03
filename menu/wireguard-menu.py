#!/usr/bin/env python3
"""
WireGuard MikroTik Management Menu
User-friendly interface for managing WireGuard VPN with MikroTik routers
"""

import os
import sys
import json
import time
import subprocess
import socket
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse

# Add project path for database integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Django components
try:
    from routers.models import Router
    from routers.services.mikrotik_api import MikroTikAPIService
    from wireguard_mikrotik_service import WireGuardMikroTikService
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Import database manager
try:
    from database_manager import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Colors and formatting
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

class WireGuardConfigManager:
    """Manages WireGuard configuration without Django"""
    
    def __init__(self):
        self.config_file = "/etc/wireguard/wg0.conf"
        self.interface = "wg0"
    
    def get_peers_from_config(self) -> List[Dict]:
        """Get peers from WireGuard configuration file"""
        peers = []
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
                
            # Parse peers from config file
            peer_blocks = re.findall(r'# (.+?)\n\[Peer\]\nPublicKey = (.+?)\nAllowedIPs = (.+?)(?=\n\n|\n#|\Z)', content, re.DOTALL)
            
            for name, public_key, allowed_ips in peer_blocks:
                peers.append({
                    'name': name.strip(),
                    'public_key': public_key.strip(),
                    'allowed_ips': allowed_ips.strip(),
                    'ip': allowed_ips.strip().split('/')[0]
                })
        except Exception as e:
            print(f"Error reading config: {e}")
        
        return peers
    
    def get_peers_from_wg_command(self) -> List[Dict]:
        """Get peers from wg command"""
        peers = []
        try:
            result = subprocess.run(['wg', 'show', self.interface, 'peers'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        peers.append({
                            'public_key': line.strip(),
                            'name': f"Peer_{line.strip()[:8]}",
                            'ip': 'Unknown',
                            'allowed_ips': 'Unknown'
                        })
        except Exception as e:
            print(f"Error running wg command: {e}")
        
        return peers
    
    def add_peer(self, name: str, public_key: str, ip: str = None) -> bool:
        """Add a peer to WireGuard configuration"""
        try:
            if not ip:
                # Get next available IP
                peers = self.get_peers_from_config()
                used_ips = [p['ip'] for p in peers if 'ip' in p]
                for i in range(2, 255):
                    candidate_ip = f"10.10.0.{i}"
                    if candidate_ip not in used_ips:
                        ip = candidate_ip
                        break
                
                if not ip:
                    print("No available IP addresses")
                    return False
            
            # Add peer to config file
            peer_config = f"\n# {name}\n[Peer]\nPublicKey = {public_key}\nAllowedIPs = {ip}/32\n"
            
            with open(self.config_file, 'a') as f:
                f.write(peer_config)
            
            # Restart WireGuard
            subprocess.run(['wg-quick', 'down', self.interface], capture_output=True)
            subprocess.run(['wg-quick', 'up', self.interface], capture_output=True)
            
            return True
        except Exception as e:
            print(f"Error adding peer: {e}")
            return False
    
    def remove_peer(self, name: str) -> bool:
        """Remove a peer from WireGuard configuration"""
        try:
            with open(self.config_file, 'r') as f:
                lines = f.readlines()
            
            # Find and remove peer block
            new_lines = []
            skip_until_next_section = False
            
            for i, line in enumerate(lines):
                if line.strip() == f"# {name}":
                    skip_until_next_section = True
                    continue
                elif skip_until_next_section and line.strip() == "[Peer]":
                    continue
                elif skip_until_next_section and line.startswith("PublicKey"):
                    continue
                elif skip_until_next_section and line.startswith("AllowedIPs"):
                    skip_until_next_section = False
                    continue
                elif not skip_until_next_section:
                    new_lines.append(line)
            
            # Write back to file
            with open(self.config_file, 'w') as f:
                f.writelines(new_lines)
            
            # Restart WireGuard
            subprocess.run(['wg-quick', 'down', self.interface], capture_output=True)
            subprocess.run(['wg-quick', 'up', self.interface], capture_output=True)
            
            return True
        except Exception as e:
            print(f"Error removing peer: {e}")
            return False

class SupabaseManager:
    """Manages Supabase integration for router data"""
    
    def __init__(self):
        self.client = None
        self.available = False
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase connection"""
        try:
            # Try to get Supabase credentials from environment or config
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                # Try to read from config file
                config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'supabase.json')
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        supabase_url = config.get('url')
                        supabase_key = config.get('key')
            
            if supabase_url and supabase_key:
                self.client = create_client(supabase_url, supabase_key)
                self.available = True
        except Exception as e:
            print(f"Supabase initialization failed: {e}")
            self.available = False
    
    def get_routers(self) -> List[Dict]:
        """Get routers from Supabase"""
        if not self.available:
            return []
        
        try:
            response = self.client.table('routers').select('*').eq('vpn_type', 'wireguard').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching routers from Supabase: {e}")
            return []
    
    def add_router(self, router_data: Dict) -> bool:
        """Add router to Supabase"""
        if not self.available:
            return False
        
        try:
            response = self.client.table('routers').insert(router_data).execute()
            return True
        except Exception as e:
            print(f"Error adding router to Supabase: {e}")
            return False

class WireGuardMenu:
    """Main menu system for WireGuard MikroTik management"""
    
    def __init__(self):
        self.wg_service = WireGuardMikroTikService() if DJANGO_AVAILABLE else None
        self.wg_config = WireGuardConfigManager()
        self.supabase = SupabaseManager()
        self.database = DatabaseManager() if DATABASE_AVAILABLE else None
        self.running = True
        self.current_page = 1
        self.items_per_page = 10
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self):
        """Print the main header"""
        print(f"{Colors.CYAN}{'='*80}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.WHITE}🔧 WireGuard MikroTik Management System{Colors.NC}")
        print(f"{Colors.CYAN}{'='*80}{Colors.NC}")
        print(f"{Colors.BLUE}📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
        print()
    
    def print_menu(self):
        """Print the main menu"""
        print(f"{Colors.BOLD}{Colors.YELLOW}📋 MAIN MENU{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
        print(f"{Colors.GREEN}1.{Colors.NC} 📊 System Status & Health Check")
        print(f"{Colors.GREEN}2.{Colors.NC} 🔌 Router Management")
        print(f"{Colors.GREEN}3.{Colors.NC} 🌐 Network Monitoring")
        print(f"{Colors.GREEN}4.{Colors.NC} ⚙️  Configuration Management")
        print(f"{Colors.GREEN}5.{Colors.NC} 🔧 Tools & Utilities")
        print(f"{Colors.GREEN}6.{Colors.NC} 📈 Performance Monitor")
        print(f"{Colors.GREEN}7.{Colors.NC} 🛡️  Security & Logs")
        print(f"{Colors.GREEN}8.{Colors.NC} 📚 Help & Documentation")
        print(f"{Colors.RED}9.{Colors.NC} 🚪 Exit")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
    
    def get_user_choice(self, max_choice: int) -> int:
        """Get user choice with validation"""
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Enter your choice (1-{max_choice}): {Colors.NC}")
                choice = int(choice)
                if 1 <= choice <= max_choice:
                    return choice
                else:
                    print(f"{Colors.RED}❌ Invalid choice. Please enter a number between 1 and {max_choice}.{Colors.NC}")
            except ValueError:
                print(f"{Colors.RED}❌ Invalid input. Please enter a number.{Colors.NC}")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.NC}")
                sys.exit(0)
    
    def wait_for_enter(self):
        """Wait for user to press Enter"""
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.NC}")
    
    def show_system_status(self):
        """Show comprehensive system status"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📊 SYSTEM STATUS & HEALTH CHECK{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        
        # Check WireGuard service
        print(f"\n{Colors.BOLD}🔧 WireGuard Service Status:{Colors.NC}")
        try:
            result = subprocess.run(["systemctl", "is-active", "wg-quick@wg0"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ WireGuard service is running{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ WireGuard service is not running{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}❌ Error checking WireGuard service: {e}{Colors.NC}")
        
        # Check WireGuard interface
        print(f"\n{Colors.BOLD}🌐 WireGuard Interface Status:{Colors.NC}")
        try:
            result = subprocess.run(["wg", "show", "wg0"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ WireGuard interface is up{Colors.NC}")
                
                # Parse and show peer information
                lines = result.stdout.split('\n')
                peers = []
                for line in lines:
                    if 'allowed ips' in line.lower():
                        peer_info = line.strip()
                        peers.append(peer_info)
                
                if peers:
                    print(f"\n{Colors.BOLD}📡 Connected Peers ({len(peers)}):{Colors.NC}")
                    for i, peer in enumerate(peers, 1):
                        print(f"  {i}. {peer}")
                else:
                    print(f"{Colors.YELLOW}⚠️  No peers connected{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ WireGuard interface is down{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}❌ Error checking WireGuard interface: {e}{Colors.NC}")
        
        # Check system resources
        print(f"\n{Colors.BOLD}💻 System Resources:{Colors.NC}")
        try:
            # Memory usage
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            
            # CPU load
            with open("/proc/loadavg", "r") as f:
                loadavg = f.read().split()[0]
            
            print(f"  CPU Load: {loadavg}")
            
            # Extract memory info
            for line in meminfo.split('\n'):
                if 'MemTotal' in line:
                    total_mem = line.split()[1]
                    print(f"  Total Memory: {int(total_mem) // 1024} MB")
                elif 'MemAvailable' in line:
                    avail_mem = line.split()[1]
                    print(f"  Available Memory: {int(avail_mem) // 1024} MB")
                    break
        except Exception as e:
            print(f"{Colors.RED}❌ Error checking system resources: {e}{Colors.NC}")
        
        # Check firewall
        print(f"\n{Colors.BOLD}🛡️  Firewall Status:{Colors.NC}")
        try:
            result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
            if "Status: active" in result.stdout:
                print(f"{Colors.GREEN}✅ Firewall is active{Colors.NC}")
                if "51820/udp" in result.stdout:
                    print(f"{Colors.GREEN}✅ WireGuard port (51820/udp) is allowed{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}⚠️  WireGuard port (51820/udp) not found in firewall rules{Colors.NC}")
            else:
                print(f"{Colors.YELLOW}⚠️  Firewall is not active{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}❌ Error checking firewall: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def show_router_management(self):
        """Show router management interface"""
        while True:
            self.clear_screen()
            self.print_header()
            
            print(f"{Colors.BOLD}{Colors.YELLOW}🔌 ROUTER MANAGEMENT{Colors.NC}")
            print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
            print(f"{Colors.GREEN}1.{Colors.NC} 📋 List All Routers")
            print(f"{Colors.GREEN}2.{Colors.NC} ➕ Add New Router")
            print(f"{Colors.GREEN}3.{Colors.NC} 🗑️  Remove Router")
            print(f"{Colors.GREEN}4.{Colors.NC} 🔄 Sync Router")
            print(f"{Colors.GREEN}5.{Colors.NC} 🔍 Test Router Connection")
            print(f"{Colors.GREEN}6.{Colors.NC} 📊 Router Status Details")
            print(f"{Colors.GREEN}7.{Colors.NC} 🔙 Back to Main Menu")
            print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
            
            choice = self.get_user_choice(7)
            
            if choice == 1:
                self.list_routers()
            elif choice == 2:
                self.add_router()
            elif choice == 3:
                self.remove_router()
            elif choice == 4:
                self.sync_router()
            elif choice == 5:
                self.test_router_connection()
            elif choice == 6:
                self.show_router_status_details()
            elif choice == 7:
                break
    
    def list_routers(self):
        """List all routers with status"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📋 ROUTER LIST{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*80}{Colors.NC}")
        
        routers = []
        
        # Priority 1: Database (same as main Django system)
        if self.database and self.database.available:
            try:
                db_routers = self.database.get_routers()
                for router in db_routers:
                    routers.append({
                        'name': router.get('name', 'Unknown'),
                        'public_key': router.get('public_key', 'Unknown'),
                        'ip': router.get('ip_address', 'Unknown'),
                        'status': 'Active' if router.get('is_active', False) else 'Inactive',
                        'source': 'Database'
                    })
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Database error: {e}{Colors.NC}")
        
        # Priority 2: Django (if available)
        if DJANGO_AVAILABLE:
            try:
                django_routers = Router.objects.filter(vpn_type="wireguard")
                for router in django_routers:
                    if not any(r['public_key'] == router.public_key for r in routers):
                        routers.append({
                            'name': router.name,
                            'public_key': router.public_key,
                            'ip': router.ip_address,
                            'status': 'Active' if router.is_active else 'Inactive',
                            'source': 'Django DB'
                        })
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Django database error: {e}{Colors.NC}")
        
        # Priority 3: Supabase (if available)
        if self.supabase.available:
            try:
                supabase_routers = self.supabase.get_routers()
                for router in supabase_routers:
                    if not any(r['public_key'] == router.get('public_key') for r in routers):
                        routers.append({
                            'name': router.get('name', 'Unknown'),
                            'public_key': router.get('public_key', 'Unknown'),
                            'ip': router.get('ip_address', 'Unknown'),
                            'status': 'Active' if router.get('is_active', False) else 'Inactive',
                            'source': 'Supabase'
                        })
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Supabase error: {e}{Colors.NC}")
        
        # Priority 4: WireGuard Config (fallback)
        try:
            wg_routers = self.wg_config.get_peers_from_config()
            for router in wg_routers:
                # Check if already added from database
                if not any(r['public_key'] == router['public_key'] for r in routers):
                    routers.append({
                        'name': router['name'],
                        'public_key': router['public_key'],
                        'ip': router['ip'],
                        'status': 'Active',
                        'source': 'WireGuard Config'
                    })
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  WireGuard config error: {e}{Colors.NC}")
        
        if not routers:
            print(f"{Colors.YELLOW}⚠️  No WireGuard routers found{Colors.NC}")
            self.wait_for_enter()
            return
        
        print(f"{Colors.BOLD}Found {len(routers)} WireGuard routers:{Colors.NC}\n")
        
        # Table header
        print(f"{'Name':<20} {'VPN IP':<15} {'Status':<10} {'Source':<15} {'Public Key':<20}")
        print(f"{Colors.CYAN}{'─'*80}{Colors.NC}")
        
        # Display routers
        for router in routers:
            status_color = Colors.GREEN if router['status'] == 'Active' else Colors.RED
            print(f"{router['name']:<20} {router['ip']:<15} {status_color}{router['status']:<10}{Colors.NC} {router['source']:<15} {router['public_key'][:20]}...")
        
        print(f"\n{Colors.CYAN}{'─'*80}{Colors.NC}")
        print(f"{Colors.BLUE}Data Sources:{Colors.NC}")
        if self.database and self.database.available:
            print(f"  {Colors.GREEN}✓{Colors.NC} Database (Primary)")
        if DJANGO_AVAILABLE:
            print(f"  {Colors.GREEN}✓{Colors.NC} Django Database")
        if self.supabase.available:
            print(f"  {Colors.GREEN}✓{Colors.NC} Supabase Database")
        print(f"  {Colors.GREEN}✓{Colors.NC} WireGuard Configuration")
        
        self.wait_for_enter()
    
    def add_router(self):
        """Add a new router"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}➕ ADD NEW ROUTER{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
        
        try:
            # Get router details
            router_name = input(f"{Colors.BOLD}Router name: {Colors.NC}")
            if not router_name:
                print(f"{Colors.RED}❌ Router name is required{Colors.NC}")
                self.wait_for_enter()
                return
            
            public_key = input(f"{Colors.BOLD}Router public key: {Colors.NC}")
            if not public_key:
                print(f"{Colors.RED}❌ Public key is required{Colors.NC}")
                self.wait_for_enter()
                return
            
            ip_address = input(f"{Colors.BOLD}VPN IP address (optional, auto-assign if empty): {Colors.NC}")
            if not ip_address.strip():
                ip_address = None
            
            print(f"\n{Colors.BLUE}Adding router...{Colors.NC}")
            
            # Add router using configuration manager
            success = self.wg_config.add_peer(router_name, public_key, ip_address)
            
            if success:
                print(f"{Colors.GREEN}✅ Router added to WireGuard configuration!{Colors.NC}")
                
                # Add to database (primary storage)
                if self.database and self.database.available:
                    router_data = {
                        'name': router_name,
                        'public_key': public_key,
                        'ip_address': ip_address or 'Auto-assigned',
                        'vpn_type': 'wireguard',
                        'is_active': True,
                        'api_accessible': False,
                        'notes': 'Added via VPS menu'
                    }
                    if self.database.add_router(router_data):
                        print(f"{Colors.GREEN}✅ Router added to database (primary storage){Colors.NC}")
                    else:
                        print(f"{Colors.YELLOW}⚠️  Router added to WireGuard but failed to add to database{Colors.NC}")
                
                # Also add to Supabase if available
                elif self.supabase.available:
                    router_data = {
                        'name': router_name,
                        'public_key': public_key,
                        'ip_address': ip_address or 'Auto-assigned',
                        'vpn_type': 'wireguard',
                        'is_active': True
                    }
                    if self.supabase.add_router(router_data):
                        print(f"{Colors.GREEN}✅ Router also added to Supabase database{Colors.NC}")
                    else:
                        print(f"{Colors.YELLOW}⚠️  Router added to WireGuard but failed to add to Supabase{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Failed to add router{Colors.NC}")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error adding router: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def remove_router(self):
        """Remove a router"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🗑️  REMOVE ROUTER{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
        
        try:
            router_name = input(f"{Colors.BOLD}Router name to remove: {Colors.NC}")
            if not router_name:
                print(f"{Colors.RED}❌ Router name is required{Colors.NC}")
                self.wait_for_enter()
                return
            
            # Confirm removal
            confirm = input(f"{Colors.YELLOW}Are you sure you want to remove '{router_name}'? (y/N): {Colors.NC}")
            if confirm.lower() != 'y':
                print(f"{Colors.BLUE}Operation cancelled{Colors.NC}")
                self.wait_for_enter()
                return
            
            # Remove router
            print(f"\n{Colors.BLUE}Removing router...{Colors.NC}")
            result = subprocess.run(["wg-mikrotik", "remove", router_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ Router removed successfully!{Colors.NC}")
                print(f"Output: {result.stdout}")
            else:
                print(f"{Colors.RED}❌ Failed to remove router{Colors.NC}")
                print(f"Error: {result.stderr}")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error removing router: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def sync_router(self):
        """Sync router with WireGuard"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🔄 SYNC ROUTER{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
        
        if not DJANGO_AVAILABLE or not self.wg_service:
            print(f"{Colors.RED}❌ Django integration not available{Colors.NC}")
            self.wait_for_enter()
            return
        
        try:
            router_name = input(f"{Colors.BOLD}Router name to sync: {Colors.NC}")
            if not router_name:
                print(f"{Colors.RED}❌ Router name is required{Colors.NC}")
                self.wait_for_enter()
                return
            
            # Find router in database
            try:
                router = Router.objects.get(name=router_name)
            except Router.DoesNotExist:
                print(f"{Colors.RED}❌ Router '{router_name}' not found in database{Colors.NC}")
                self.wait_for_enter()
                return
            
            # Sync router
            print(f"\n{Colors.BLUE}Syncing router...{Colors.NC}")
            success, message = self.wg_service.sync_router_with_wireguard(router)
            
            if success:
                print(f"{Colors.GREEN}✅ {message}{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ {message}{Colors.NC}")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error syncing router: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def test_router_connection(self):
        """Test router connection"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🔍 TEST ROUTER CONNECTION{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
        
        try:
            router_ip = input(f"{Colors.BOLD}Router VPN IP address: {Colors.NC}")
            if not router_ip:
                print(f"{Colors.RED}❌ Router IP is required{Colors.NC}")
                self.wait_for_enter()
                return
            
            print(f"\n{Colors.BLUE}Testing connection to {router_ip}...{Colors.NC}")
            
            # Test ping
            print(f"{Colors.BLUE}1. Testing ping...{Colors.NC}")
            ping_result = subprocess.run(["ping", "-c", "3", "-W", "5", router_ip], 
                                       capture_output=True, text=True)
            
            if ping_result.returncode == 0:
                print(f"{Colors.GREEN}✅ Ping successful{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Ping failed{Colors.NC}")
                print(f"Error: {ping_result.stderr}")
                self.wait_for_enter()
                return
            
            # Test API port
            print(f"{Colors.BLUE}2. Testing API port (8728)...{Colors.NC}")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((router_ip, 8728))
                sock.close()
                
                if result == 0:
                    print(f"{Colors.GREEN}✅ API port is accessible{Colors.NC}")
                else:
                    print(f"{Colors.RED}❌ API port is not accessible{Colors.NC}")
            except Exception as e:
                print(f"{Colors.RED}❌ Error testing API port: {e}{Colors.NC}")
            
            # Test API connection if credentials available
            username = input(f"\n{Colors.BOLD}Router username (optional): {Colors.NC}")
            if username:
                password = input(f"{Colors.BOLD}Router password (optional): {Colors.NC}")
                if password:
                    print(f"{Colors.BLUE}3. Testing API connection...{Colors.NC}")
                    # This would require the full API test implementation
                    print(f"{Colors.YELLOW}⚠️  API connection test requires full implementation{Colors.NC}")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error testing connection: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def show_router_status_details(self):
        """Show detailed router status"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📊 ROUTER STATUS DETAILS{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        
        if not DJANGO_AVAILABLE or not self.wg_service:
            print(f"{Colors.RED}❌ Django integration not available{Colors.NC}")
            self.wait_for_enter()
            return
        
        try:
            # Get all router status
            all_status = self.wg_service.get_all_vpn_status()
            
            print(f"{Colors.BOLD}Overall Status:{Colors.NC}")
            print(f"  Total Routers: {all_status['total_routers']}")
            print(f"  Online: {all_status['online_routers']}")
            print(f"  Offline: {all_status['offline_routers']}")
            print()
            
            # Show individual router details
            for router_info in all_status['routers']:
                print(f"{Colors.BOLD}Router: {router_info['name']} ({router_info['vpn_ip']}){Colors.NC}")
                status = router_info['status']
                
                print(f"  Status: {'Online' if status['is_connected'] else 'Offline'}")
                print(f"  API Accessible: {'Yes' if status.get('api_accessible', False) else 'No'}")
                print(f"  Last Check: {status.get('last_check', 'Never')}")
                
                if status.get('message'):
                    print(f"  Message: {status['message']}")
                print()
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting router status: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def show_network_monitoring(self):
        """Show network monitoring interface"""
        while True:
            self.clear_screen()
            self.print_header()
            
            print(f"{Colors.BOLD}{Colors.YELLOW}🌐 NETWORK MONITORING{Colors.NC}")
            print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
            print(f"{Colors.GREEN}1.{Colors.NC} 📊 Real-time Status")
            print(f"{Colors.GREEN}2.{Colors.NC} 🔄 Continuous Monitoring")
            print(f"{Colors.GREEN}3.{Colors.NC} 📈 Bandwidth Usage")
            print(f"{Colors.GREEN}4.{Colors.NC} 🚨 Alert History")
            print(f"{Colors.GREEN}5.{Colors.NC} 🔙 Back to Main Menu")
            print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
            
            choice = self.get_user_choice(5)
            
            if choice == 1:
                self.show_realtime_status()
            elif choice == 2:
                self.start_continuous_monitoring()
            elif choice == 3:
                self.show_bandwidth_usage()
            elif choice == 4:
                self.show_alert_history()
            elif choice == 5:
                break
    
    def show_realtime_status(self):
        """Show real-time network status"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📊 REAL-TIME STATUS{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        
        try:
            # Get WireGuard status
            result = subprocess.run(["wg", "show", "wg0"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ WireGuard is running{Colors.NC}")
                
                # Parse peer information
                lines = result.stdout.split('\n')
                peers = []
                for line in lines:
                    if 'allowed ips' in line.lower():
                        peer_info = line.strip()
                        peers.append(peer_info)
                
                if peers:
                    print(f"\n{Colors.BOLD}Connected Peers ({len(peers)}):{Colors.NC}")
                    for i, peer in enumerate(peers, 1):
                        print(f"  {i}. {peer}")
                else:
                    print(f"{Colors.YELLOW}⚠️  No peers connected{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ WireGuard is not running{Colors.NC}")
            
            # Show system load
            print(f"\n{Colors.BOLD}System Load:{Colors.NC}")
            with open("/proc/loadavg", "r") as f:
                loadavg = f.read().split()
            print(f"  1min: {loadavg[0]}, 5min: {loadavg[1]}, 15min: {loadavg[2]}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting real-time status: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def start_continuous_monitoring(self):
        """Start continuous monitoring"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🔄 CONTINUOUS MONITORING{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        print(f"{Colors.YELLOW}Press Ctrl+C to stop monitoring{Colors.NC}")
        print()
        
        try:
            while True:
                # Clear screen and show header
                self.clear_screen()
                self.print_header()
                print(f"{Colors.BOLD}{Colors.YELLOW}🔄 CONTINUOUS MONITORING{Colors.NC}")
                print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
                print(f"{Colors.BLUE}Last updated: {datetime.now().strftime('%H:%M:%S')}{Colors.NC}")
                print()
                
                # Get WireGuard status
                result = subprocess.run(["wg", "show", "wg0"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✅ WireGuard: Running{Colors.NC}")
                    
                    # Count peers
                    lines = result.stdout.split('\n')
                    peer_count = sum(1 for line in lines if 'allowed ips' in line.lower())
                    print(f"📡 Connected Peers: {peer_count}")
                else:
                    print(f"{Colors.RED}❌ WireGuard: Not Running{Colors.NC}")
                
                # Show system load
                with open("/proc/loadavg", "r") as f:
                    loadavg = f.read().split()
                print(f"💻 CPU Load: {loadavg[0]}")
                
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Monitoring stopped{Colors.NC}")
            self.wait_for_enter()
    
    def show_bandwidth_usage(self):
        """Show bandwidth usage"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📈 BANDWIDTH USAGE{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        
        try:
            # Get WireGuard statistics
            result = subprocess.run(["wg", "show", "wg0"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ WireGuard Statistics:{Colors.NC}")
                print(result.stdout)
            else:
                print(f"{Colors.RED}❌ Cannot get WireGuard statistics{Colors.NC}")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting bandwidth usage: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def show_alert_history(self):
        """Show alert history"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🚨 ALERT HISTORY{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        
        try:
            # Check WireGuard logs
            result = subprocess.run(["journalctl", "-u", "wg-quick@wg0", "--no-pager", "-n", "20"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.BOLD}Recent WireGuard Logs:{Colors.NC}")
                print(result.stdout)
            else:
                print(f"{Colors.YELLOW}⚠️  No WireGuard logs available{Colors.NC}")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting alert history: {e}{Colors.NC}")
        
        self.wait_for_enter()
    
    def run(self):
        """Run the main menu loop"""
        while self.running:
            self.clear_screen()
            self.print_header()
            self.print_menu()
            
            choice = self.get_user_choice(9)
            
            if choice == 1:
                self.show_system_status()
            elif choice == 2:
                self.show_router_management()
            elif choice == 3:
                self.show_network_monitoring()
            elif choice == 4:
                self.show_configuration_management()
            elif choice == 5:
                self.show_tools_utilities()
            elif choice == 6:
                self.show_performance_monitor()
            elif choice == 7:
                self.show_security_logs()
            elif choice == 8:
                self.show_help_documentation()
            elif choice == 9:
                print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.NC}")
                self.running = False
    
    def show_configuration_management(self):
        """Show configuration management interface"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}⚙️  CONFIGURATION MANAGEMENT{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        print(f"{Colors.YELLOW}This feature is under development{Colors.NC}")
        print(f"{Colors.BLUE}Will include:{Colors.NC}")
        print(f"  • View WireGuard configuration")
        print(f"  • Edit configuration files")
        print(f"  • Backup/restore configurations")
        print(f"  • Generate router configs")
        
        self.wait_for_enter()
    
    def show_tools_utilities(self):
        """Show tools and utilities"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🔧 TOOLS & UTILITIES{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        print(f"{Colors.YELLOW}This feature is under development{Colors.NC}")
        print(f"{Colors.BLUE}Will include:{Colors.NC}")
        print(f"  • Test connectivity tools")
        print(f"  • Generate reports")
        print(f"  • Export configurations")
        print(f"  • System diagnostics")
        
        self.wait_for_enter()
    
    def show_performance_monitor(self):
        """Show performance monitoring"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📈 PERFORMANCE MONITOR{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        print(f"{Colors.YELLOW}This feature is under development{Colors.NC}")
        print(f"{Colors.BLUE}Will include:{Colors.NC}")
        print(f"  • CPU and memory usage")
        print(f"  • Network throughput")
        print(f"  • Connection quality metrics")
        print(f"  • Performance alerts")
        
        self.wait_for_enter()
    
    def show_security_logs(self):
        """Show security and logs"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🛡️  SECURITY & LOGS{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        print(f"{Colors.YELLOW}This feature is under development{Colors.NC}")
        print(f"{Colors.BLUE}Will include:{Colors.NC}")
        print(f"  • Security audit logs")
        print(f"  • Access logs")
        print(f"  • Firewall status")
        print(f"  • Key management")
        
        self.wait_for_enter()
    
    def show_help_documentation(self):
        """Show help and documentation"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📚 HELP & DOCUMENTATION{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.NC}")
        print(f"{Colors.BOLD}WireGuard MikroTik Management System{Colors.NC}")
        print()
        print(f"{Colors.BOLD}Features:{Colors.NC}")
        print(f"  • Complete WireGuard VPN management")
        print(f"  • Multiple MikroTik router support")
        print(f"  • Real-time monitoring and status")
        print(f"  • Django integration")
        print(f"  • User-friendly interface")
        print()
        print(f"{Colors.BOLD}Quick Start:{Colors.NC}")
        print(f"  1. Install WireGuard: sudo bash install-wireguard-vps.sh")
        print(f"  2. Generate configs: ./mikrotik-wireguard-setup.sh")
        print(f"  3. Configure routers with .rsc files")
        print(f"  4. Use this menu to manage everything")
        print()
        print(f"{Colors.BOLD}For more help:{Colors.NC}")
        print(f"  • Read WIREGUARD_MIKROTIK_SETUP.md")
        print(f"  • Check logs: journalctl -u wg-quick@wg0")
        print(f"  • Test setup: python3 test-wireguard-setup.py")
        
        self.wait_for_enter()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="WireGuard MikroTik Management Menu")
    parser.add_argument("--no-django", action="store_true", help="Run without Django integration")
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print(f"{Colors.RED}❌ This script must be run as root (use sudo){Colors.NC}")
        sys.exit(1)
    
    # Create and run menu
    menu = WireGuardMenu()
    menu.run()

if __name__ == "__main__":
    main()
