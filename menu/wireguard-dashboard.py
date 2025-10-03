#!/usr/bin/env python3
"""
WireGuard MikroTik Dashboard
Real-time dashboard for monitoring WireGuard VPN with MikroTik routers
"""

import os
import sys
import json
import time
import subprocess
import socket
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse

# Add project path for Django integration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from routers.models import Router
    from routers.services.mikrotik_api import MikroTikAPIService
    from wireguard_mikrotik_service import WireGuardMikroTikService
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

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

class WireGuardDashboard:
    """Real-time dashboard for WireGuard monitoring"""
    
    def __init__(self):
        self.wg_service = WireGuardMikroTikService() if DJANGO_AVAILABLE else None
        self.running = True
        self.refresh_interval = 5  # seconds
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self):
        """Print the dashboard header"""
        print(f"{Colors.CYAN}{'='*100}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.WHITE}🔧 WireGuard MikroTik Dashboard{Colors.NC}")
        print(f"{Colors.CYAN}{'='*100}{Colors.NC}")
        print(f"{Colors.BLUE}📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🔄 Auto-refresh every {self.refresh_interval}s{Colors.NC}")
        print()
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        status = {
            "wireguard_service": False,
            "wireguard_interface": False,
            "firewall": False,
            "peers": [],
            "system_load": "0.00",
            "memory_usage": 0,
            "uptime": "0:00"
        }
        
        try:
            # Check WireGuard service
            result = subprocess.run(["systemctl", "is-active", "wg-quick@wg0"], 
                                  capture_output=True, text=True)
            status["wireguard_service"] = result.returncode == 0
            
            # Check WireGuard interface
            result = subprocess.run(["wg", "show", "wg0"], capture_output=True, text=True)
            if result.returncode == 0:
                status["wireguard_interface"] = True
                
                # Parse peer information
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'allowed ips' in line.lower():
                        peer_info = line.strip()
                        status["peers"].append(peer_info)
            
            # Check firewall
            result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
            status["firewall"] = "Status: active" in result.stdout
            
            # Get system load
            with open("/proc/loadavg", "r") as f:
                loadavg = f.read().split()
            status["system_load"] = loadavg[0]
            
            # Get memory usage
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            
            for line in meminfo.split('\n'):
                if 'MemTotal' in line:
                    total_mem = int(line.split()[1])
                elif 'MemAvailable' in line:
                    avail_mem = int(line.split()[1])
                    status["memory_usage"] = round((total_mem - avail_mem) / total_mem * 100, 1)
                    break
            
            # Get uptime
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                status["uptime"] = f"{hours}:{minutes:02d}"
            
        except Exception as e:
            print(f"{Colors.RED}Error getting system status: {e}{Colors.NC}")
        
        return status
    
    def get_router_status(self) -> List[Dict]:
        """Get status of all routers"""
        routers = []
        
        if not DJANGO_AVAILABLE or not self.wg_service:
            return routers
        
        try:
            # Get all router status
            all_status = self.wg_service.get_all_vpn_status()
            
            for router_info in all_status.get('routers', []):
                router = {
                    "name": router_info['name'],
                    "vpn_ip": router_info['vpn_ip'],
                    "is_online": router_info['status']['is_connected'],
                    "api_accessible": router_info['status'].get('api_accessible', False),
                    "last_check": router_info['status'].get('last_check', 'Never'),
                    "status": router_info['status'].get('status', 'unknown')
                }
                routers.append(router)
        
        except Exception as e:
            print(f"{Colors.RED}Error getting router status: {e}{Colors.NC}")
        
        return routers
    
    def print_system_overview(self, status: Dict):
        """Print system overview section"""
        print(f"{Colors.BOLD}{Colors.YELLOW}📊 SYSTEM OVERVIEW{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
        
        # WireGuard Service Status
        if status["wireguard_service"]:
            print(f"{Colors.GREEN}✅ WireGuard Service: Running{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ WireGuard Service: Stopped{Colors.NC}")
        
        # WireGuard Interface Status
        if status["wireguard_interface"]:
            print(f"{Colors.GREEN}✅ WireGuard Interface: Up{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ WireGuard Interface: Down{Colors.NC}")
        
        # Firewall Status
        if status["firewall"]:
            print(f"{Colors.GREEN}✅ Firewall: Active{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⚠️  Firewall: Inactive{Colors.NC}")
        
        # System Resources
        print(f"💻 CPU Load: {status['system_load']}")
        print(f"🧠 Memory Usage: {status['memory_usage']}%")
        print(f"⏱️  System Uptime: {status['uptime']}")
        
        # Connected Peers
        peer_count = len(status["peers"])
        if peer_count > 0:
            print(f"📡 Connected Peers: {peer_count}")
        else:
            print(f"{Colors.YELLOW}⚠️  No peers connected{Colors.NC}")
        
        print()
    
    def print_router_table(self, routers: List[Dict]):
        """Print router status table"""
        print(f"{Colors.BOLD}{Colors.YELLOW}🔌 ROUTER STATUS{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*100}{Colors.NC}")
        
        if not routers:
            print(f"{Colors.YELLOW}No routers found in database{Colors.NC}")
            return
        
        # Table header
        print(f"{'Name':<20} {'VPN IP':<15} {'Status':<12} {'API':<8} {'Last Check':<20} {'Details':<20}")
        print(f"{Colors.CYAN}{'─'*100}{Colors.NC}")
        
        for router in routers:
            # Format status
            if router["is_online"]:
                status_text = f"{Colors.GREEN}Online{Colors.NC}"
            else:
                status_text = f"{Colors.RED}Offline{Colors.NC}"
            
            # Format API status
            if router["api_accessible"]:
                api_text = f"{Colors.GREEN}Yes{Colors.NC}"
            else:
                api_text = f"{Colors.RED}No{Colors.NC}"
            
            # Format last check
            last_check = router["last_check"]
            if last_check != "Never":
                try:
                    # Try to format the timestamp
                    if isinstance(last_check, str) and 'T' in last_check:
                        dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                        last_check = dt.strftime('%m-%d %H:%M')
                except:
                    pass
            
            # Format details
            details = router["status"]
            if details == "online":
                details = f"{Colors.GREEN}Connected{Colors.NC}"
            elif details == "offline":
                details = f"{Colors.RED}Disconnected{Colors.NC}"
            else:
                details = f"{Colors.YELLOW}{details}{Colors.NC}"
            
            print(f"{router['name']:<20} {router['vpn_ip']:<15} {status_text:<20} {api_text:<12} {last_check:<20} {details:<20}")
        
        print()
    
    def print_peer_details(self, peers: List[str]):
        """Print detailed peer information"""
        if not peers:
            return
        
        print(f"{Colors.BOLD}{Colors.YELLOW}📡 WIREGUARD PEERS{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*80}{Colors.NC}")
        
        for i, peer in enumerate(peers, 1):
            print(f"{i:2d}. {peer}")
        
        print()
    
    def print_quick_actions(self):
        """Print quick action buttons"""
        print(f"{Colors.BOLD}{Colors.YELLOW}⚡ QUICK ACTIONS{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
        print(f"{Colors.GREEN}1.{Colors.NC} 🔄 Refresh Now")
        print(f"{Colors.GREEN}2.{Colors.NC} 🔧 Open Management Menu")
        print(f"{Colors.GREEN}3.{Colors.NC} 📊 Show Detailed Logs")
        print(f"{Colors.GREEN}4.{Colors.NC} 🧪 Run System Test")
        print(f"{Colors.GREEN}5.{Colors.NC} ⚙️  Change Refresh Rate")
        print(f"{Colors.RED}6.{Colors.NC} 🚪 Exit Dashboard")
        print(f"{Colors.CYAN}{'─'*50}{Colors.NC}")
    
    def handle_quick_action(self, choice: int):
        """Handle quick action selection"""
        if choice == 1:
            return  # Refresh now
        elif choice == 2:
            self.open_management_menu()
        elif choice == 3:
            self.show_detailed_logs()
        elif choice == 4:
            self.run_system_test()
        elif choice == 5:
            self.change_refresh_rate()
        elif choice == 6:
            self.running = False
    
    def open_management_menu(self):
        """Open the management menu"""
        print(f"\n{Colors.BLUE}Opening management menu...{Colors.NC}")
        try:
            subprocess.run([sys.executable, "wireguard-menu.py"])
        except Exception as e:
            print(f"{Colors.RED}Error opening management menu: {e}{Colors.NC}")
        input(f"\n{Colors.CYAN}Press Enter to return to dashboard...{Colors.NC}")
    
    def show_detailed_logs(self):
        """Show detailed logs"""
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.YELLOW}📊 DETAILED LOGS{Colors.NC}")
        print(f"{Colors.CYAN}{'─'*80}{Colors.NC}")
        
        try:
            # Show WireGuard logs
            result = subprocess.run(["journalctl", "-u", "wg-quick@wg0", "--no-pager", "-n", "50"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"{Colors.YELLOW}No WireGuard logs available{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}Error getting logs: {e}{Colors.NC}")
        
        input(f"\n{Colors.CYAN}Press Enter to return to dashboard...{Colors.NC}")
    
    def run_system_test(self):
        """Run system test"""
        print(f"\n{Colors.BLUE}Running system test...{Colors.NC}")
        try:
            result = subprocess.run([sys.executable, "test-wireguard-setup.py"], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"{Colors.RED}Errors:{Colors.NC}")
                print(result.stderr)
        except Exception as e:
            print(f"{Colors.RED}Error running system test: {e}{Colors.NC}")
        
        input(f"\n{Colors.CYAN}Press Enter to return to dashboard...{Colors.NC}")
    
    def change_refresh_rate(self):
        """Change refresh rate"""
        print(f"\n{Colors.BOLD}Current refresh rate: {self.refresh_interval} seconds{Colors.NC}")
        try:
            new_rate = input(f"Enter new refresh rate (1-60 seconds): ")
            new_rate = int(new_rate)
            if 1 <= new_rate <= 60:
                self.refresh_interval = new_rate
                print(f"{Colors.GREEN}Refresh rate changed to {new_rate} seconds{Colors.NC}")
            else:
                print(f"{Colors.RED}Invalid rate. Must be between 1 and 60 seconds{Colors.NC}")
        except ValueError:
            print(f"{Colors.RED}Invalid input. Please enter a number{Colors.NC}")
        
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.NC}")
    
    def run_dashboard(self):
        """Run the main dashboard loop"""
        while self.running:
            self.clear_screen()
            self.print_header()
            
            # Get system status
            system_status = self.get_system_status()
            
            # Get router status
            router_status = self.get_router_status()
            
            # Print system overview
            self.print_system_overview(system_status)
            
            # Print router table
            self.print_router_table(router_status)
            
            # Print peer details
            self.print_peer_details(system_status["peers"])
            
            # Print quick actions
            self.print_quick_actions()
            
            # Handle user input (non-blocking)
            try:
                # Check if user pressed a key (non-blocking)
                import select
                import sys
                
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    choice = input(f"\n{Colors.BOLD}Enter choice (1-6) or press Enter to refresh: {Colors.NC}")
                    if choice.strip():
                        try:
                            choice_num = int(choice)
                            if 1 <= choice_num <= 6:
                                self.handle_quick_action(choice_num)
                                if choice_num != 1:  # Don't refresh if not choice 1
                                    continue
                        except ValueError:
                            pass
                
                # Wait for refresh interval
                time.sleep(self.refresh_interval)
                
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Dashboard stopped{Colors.NC}")
                self.running = False
            except Exception as e:
                print(f"\n{Colors.RED}Error in dashboard: {e}{Colors.NC}")
                time.sleep(self.refresh_interval)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="WireGuard MikroTik Dashboard")
    parser.add_argument("--refresh", type=int, default=5, help="Refresh rate in seconds (1-60)")
    parser.add_argument("--no-django", action="store_true", help="Run without Django integration")
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print(f"{Colors.RED}❌ This script must be run as root (use sudo){Colors.NC}")
        sys.exit(1)
    
    # Create and run dashboard
    dashboard = WireGuardDashboard()
    if 1 <= args.refresh <= 60:
        dashboard.refresh_interval = args.refresh
    
    try:
        dashboard.run_dashboard()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.NC}")

if __name__ == "__main__":
    main()
