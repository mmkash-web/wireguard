#!/usr/bin/env python3
"""
MikroTik Router Connection Validator
Validates individual MikroTik router connections via WireGuard VPN
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
    print("Warning: Django models not available. Running in standalone mode.")

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def print_status(message: str, status: str = "INFO"):
    """Print colored status message"""
    color_map = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "HEADER": Colors.CYAN,
        "DETAIL": Colors.PURPLE
    }
    color = color_map.get(status, Colors.WHITE)
    print(f"{color}[{status}]{Colors.NC} {message}")

class MikroTikConnectionValidator:
    """Validator for MikroTik router connections"""
    
    def __init__(self):
        self.wg_service = WireGuardMikroTikService() if DJANGO_AVAILABLE else None
        self.test_results = []
    
    def validate_router(self, router_ip: str, router_name: str = None, 
                      username: str = "admin", password: str = None) -> Dict:
        """
        Validate a single MikroTik router connection
        
        Args:
            router_ip: Router VPN IP address
            router_name: Router name (optional)
            username: Router username
            password: Router password (optional)
        
        Returns:
            Dictionary with validation results
        """
        if not router_name:
            router_name = f"router-{router_ip.split('.')[-1]}"
        
        print_status(f"Validating router: {router_name} ({router_ip})", "HEADER")
        print("-" * 50)
        
        results = {
            "router_name": router_name,
            "router_ip": router_ip,
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "overall_status": "PASS",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": 0
        }
        
        # Test 1: Basic connectivity
        connectivity_result = self._test_connectivity(router_ip)
        results["tests"].append(connectivity_result)
        
        if connectivity_result["status"] != "PASS":
            results["overall_status"] = "FAIL"
            self._print_test_result(connectivity_result)
            return results
        
        # Test 2: Port accessibility
        port_result = self._test_port_access(router_ip, 8728)
        results["tests"].append(port_result)
        
        # Test 3: API connectivity (if password provided)
        if password:
            api_result = self._test_api_connectivity(router_ip, username, password)
            results["tests"].append(api_result)
        else:
            api_result = {
                "name": "API connectivity",
                "status": "SKIP",
                "message": "No password provided - skipping API test"
            }
            results["tests"].append(api_result)
        
        # Test 4: WireGuard status
        wg_result = self._test_wireguard_status(router_ip)
        results["tests"].append(wg_result)
        
        # Test 5: System information (if API available)
        if password and api_result["status"] == "PASS":
            sys_result = self._test_system_info(router_ip, username, password)
            results["tests"].append(sys_result)
        else:
            sys_result = {
                "name": "System information",
                "status": "SKIP",
                "message": "API not available - skipping system info test"
            }
            results["tests"].append(sys_result)
        
        # Calculate summary
        results["total_tests"] = len(results["tests"])
        results["passed_tests"] = sum(1 for t in results["tests"] if t["status"] == "PASS")
        results["failed_tests"] = sum(1 for t in results["tests"] if t["status"] == "FAIL")
        results["warnings"] = sum(1 for t in results["tests"] if t["status"] == "WARNING")
        
        # Determine overall status
        if results["failed_tests"] > 0:
            results["overall_status"] = "FAIL"
        elif results["warnings"] > 0:
            results["overall_status"] = "WARNING"
        
        # Print results
        for test in results["tests"]:
            self._print_test_result(test)
        
        return results
    
    def validate_all_routers(self) -> Dict:
        """Validate all routers from Django database"""
        if not DJANGO_AVAILABLE:
            return {
                "error": "Django not available",
                "message": "Cannot validate all routers without Django integration"
            }
        
        print_status("Validating all routers from database", "HEADER")
        print("=" * 60)
        
        routers = Router.objects.filter(vpn_type="wireguard", vpn_ip__isnull=False)
        
        if not routers.exists():
            print_status("No WireGuard routers found in database", "WARNING")
            return {
                "total_routers": 0,
                "validated_routers": 0,
                "overall_status": "WARNING",
                "message": "No routers to validate"
            }
        
        all_results = {
            "total_routers": routers.count(),
            "validated_routers": 0,
            "overall_status": "PASS",
            "routers": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        
        for router in routers:
            print(f"\nValidating router: {router.name}")
            result = self.validate_router(
                router_ip=router.vpn_ip,
                router_name=router.name,
                username=router.username,
                password=router.password
            )
            
            all_results["routers"].append(result)
            all_results["validated_routers"] += 1
            
            # Update summary
            if result["overall_status"] == "PASS":
                all_results["summary"]["passed"] += 1
            elif result["overall_status"] == "FAIL":
                all_results["summary"]["failed"] += 1
                all_results["overall_status"] = "FAIL"
            else:
                all_results["summary"]["warnings"] += 1
                if all_results["overall_status"] != "FAIL":
                    all_results["overall_status"] = "WARNING"
        
        # Print summary
        self._print_summary(all_results)
        return all_results
    
    def _test_connectivity(self, router_ip: str) -> Dict:
        """Test basic connectivity to router"""
        try:
            result = subprocess.run(
                ["ping", "-c", "3", "-W", "5", router_ip],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Extract ping statistics
                lines = result.stdout.split('\n')
                stats_line = [line for line in lines if "packets transmitted" in line]
                if stats_line:
                    return {
                        "name": "Basic connectivity",
                        "status": "PASS",
                        "message": f"Ping successful - {stats_line[0].strip()}"
                    }
                else:
                    return {
                        "name": "Basic connectivity",
                        "status": "PASS",
                        "message": "Ping successful"
                    }
            else:
                return {
                    "name": "Basic connectivity",
                    "status": "FAIL",
                    "message": f"Ping failed - {result.stderr.strip()}"
                }
        except Exception as e:
            return {
                "name": "Basic connectivity",
                "status": "ERROR",
                "message": f"Error testing connectivity: {str(e)}"
            }
    
    def _test_port_access(self, router_ip: str, port: int) -> Dict:
        """Test if a specific port is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((router_ip, port))
            sock.close()
            
            if result == 0:
                return {
                    "name": f"Port {port} access",
                    "status": "PASS",
                    "message": f"Port {port} is accessible"
                }
            else:
                return {
                    "name": f"Port {port} access",
                    "status": "FAIL",
                    "message": f"Port {port} is not accessible"
                }
        except Exception as e:
            return {
                "name": f"Port {port} access",
                "status": "ERROR",
                "message": f"Error testing port {port}: {str(e)}"
            }
    
    def _test_api_connectivity(self, router_ip: str, username: str, password: str) -> Dict:
        """Test MikroTik API connectivity"""
        if not DJANGO_AVAILABLE:
            return {
                "name": "API connectivity",
                "status": "SKIP",
                "message": "Django not available - cannot test API"
            }
        
        try:
            # Create a mock router object for testing
            class MockRouter:
                def __init__(self, ip, user, pwd):
                    self.vpn_ip = ip
                    self.username = user
                    self.password = pwd
                    self.api_port = 8728
            
            mock_router = MockRouter(router_ip, username, password)
            
            with MikroTikAPIService(mock_router) as api:
                # Try to get system resource info
                success, info = api.check_status()
                
                if success:
                    return {
                        "name": "API connectivity",
                        "status": "PASS",
                        "message": f"API connected successfully - Router: {info.get('identity', 'Unknown')}"
                    }
                else:
                    return {
                        "name": "API connectivity",
                        "status": "FAIL",
                        "message": f"API connection failed: {info.get('error', 'Unknown error')}"
                    }
        except Exception as e:
            return {
                "name": "API connectivity",
                "status": "ERROR",
                "message": f"Error testing API: {str(e)}"
            }
    
    def _test_wireguard_status(self, router_ip: str) -> Dict:
        """Test WireGuard status on the router"""
        try:
            # Try to get WireGuard status from VPS
            result = subprocess.run(
                ["wg", "show", "wg0"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Look for the router IP in the output
                if router_ip in result.stdout:
                    return {
                        "name": "WireGuard status",
                        "status": "PASS",
                        "message": f"Router {router_ip} found in WireGuard peers"
                    }
                else:
                    return {
                        "name": "WireGuard status",
                        "status": "WARNING",
                        "message": f"Router {router_ip} not found in WireGuard peers"
                    }
            else:
                return {
                    "name": "WireGuard status",
                    "status": "ERROR",
                    "message": "Cannot get WireGuard status from VPS"
                }
        except Exception as e:
            return {
                "name": "WireGuard status",
                "status": "ERROR",
                "message": f"Error checking WireGuard status: {str(e)}"
            }
    
    def _test_system_info(self, router_ip: str, username: str, password: str) -> Dict:
        """Test system information retrieval"""
        if not DJANGO_AVAILABLE:
            return {
                "name": "System information",
                "status": "SKIP",
                "message": "Django not available - cannot test system info"
            }
        
        try:
            class MockRouter:
                def __init__(self, ip, user, pwd):
                    self.vpn_ip = ip
                    self.username = user
                    self.password = pwd
                    self.api_port = 8728
            
            mock_router = MockRouter(router_ip, username, password)
            
            with MikroTikAPIService(mock_router) as api:
                success, info = api.check_status()
                
                if success:
                    details = []
                    if info.get('version'):
                        details.append(f"Version: {info['version']}")
                    if info.get('platform'):
                        details.append(f"Platform: {info['platform']}")
                    if info.get('uptime'):
                        details.append(f"Uptime: {info['uptime']}")
                    
                    return {
                        "name": "System information",
                        "status": "PASS",
                        "message": f"System info retrieved - {', '.join(details)}"
                    }
                else:
                    return {
                        "name": "System information",
                        "status": "FAIL",
                        "message": f"Failed to get system info: {info.get('error', 'Unknown error')}"
                    }
        except Exception as e:
            return {
                "name": "System information",
                "status": "ERROR",
                "message": f"Error getting system info: {str(e)}"
            }
    
    def _print_test_result(self, test: Dict):
        """Print individual test result"""
        status_color = {
            "PASS": Colors.GREEN,
            "FAIL": Colors.RED,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "SKIP": Colors.CYAN
        }.get(test["status"], Colors.WHITE)
        
        print(f"  {status_color}[{test['status']}]{Colors.NC} {test['name']}: {test['message']}")
    
    def _print_summary(self, results: Dict):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print_status("VALIDATION SUMMARY", "HEADER")
        print("=" * 60)
        
        print(f"Total Routers: {results['total_routers']}")
        print(f"Validated: {results['validated_routers']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Warnings: {results['summary']['warnings']}")
        print(f"Overall Status: {results['overall_status']}")
        
        print("\nRouter Details:")
        print("-" * 40)
        
        for router in results["routers"]:
            status_color = {
                "PASS": Colors.GREEN,
                "FAIL": Colors.RED,
                "WARNING": Colors.YELLOW
            }.get(router["overall_status"], Colors.WHITE)
            
            print(f"{status_color}[{router['overall_status']}]{Colors.NC} {router['router_name']} "
                  f"({router['router_ip']}): {router['passed_tests']}/{router['total_tests']} tests passed")
        
        print("=" * 60)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MikroTik Router Connection Validator")
    parser.add_argument("--router-ip", help="Router VPN IP address")
    parser.add_argument("--router-name", help="Router name")
    parser.add_argument("--username", default="admin", help="Router username")
    parser.add_argument("--password", help="Router password")
    parser.add_argument("--all", action="store_true", help="Validate all routers from database")
    parser.add_argument("--output", "-o", help="Output results to JSON file")
    
    args = parser.parse_args()
    
    validator = MikroTikConnectionValidator()
    
    if args.all:
        if not DJANGO_AVAILABLE:
            print_status("Django not available. Cannot validate all routers.", "ERROR")
            sys.exit(1)
        
        results = validator.validate_all_routers()
    elif args.router_ip:
        results = validator.validate_router(
            router_ip=args.router_ip,
            router_name=args.router_name,
            username=args.username,
            password=args.password
        )
    else:
        print_status("Please specify --router-ip or --all", "ERROR")
        parser.print_help()
        sys.exit(1)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print_status(f"Results saved to: {args.output}", "INFO")
    
    # Exit with appropriate code
    if isinstance(results, dict) and "overall_status" in results:
        if results["overall_status"] == "PASS":
            sys.exit(0)
        elif results["overall_status"] == "WARNING":
            sys.exit(1)
        else:
            sys.exit(2)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
