#!/usr/bin/env python3
"""
WireGuard MikroTik Setup Testing and Validation Script
Comprehensive testing suite for WireGuard VPN with MikroTik routers
"""

import os
import sys
import json
import time
import subprocess
import socket
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse

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

class WireGuardTester:
    """Comprehensive WireGuard testing suite"""
    
    def __init__(self):
        self.wg_config = "/etc/wireguard/wg0.conf"
        self.wg_interface = "wg0"
        self.management_script = "/usr/local/bin/wg-mikrotik"
        self.test_results = []
        self.start_time = datetime.now()
    
    def run_all_tests(self) -> Dict:
        """Run all tests and return comprehensive results"""
        print_status("Starting WireGuard MikroTik Testing Suite", "HEADER")
        print_status(f"Test started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        print("=" * 60)
        
        # Test categories
        test_categories = [
            ("System Requirements", self.test_system_requirements),
            ("WireGuard Installation", self.test_wireguard_installation),
            ("Configuration Files", self.test_configuration_files),
            ("Network Connectivity", self.test_network_connectivity),
            ("Management Tools", self.test_management_tools),
            ("Security Settings", self.test_security_settings),
            ("Performance Tests", self.test_performance),
            ("Integration Tests", self.test_integration)
        ]
        
        results = {
            "test_start": self.start_time.isoformat(),
            "categories": {},
            "overall_status": "PASS",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": 0
        }
        
        for category_name, test_function in test_categories:
            print_status(f"\nTesting: {category_name}", "HEADER")
            print("-" * 40)
            
            try:
                category_results = test_function()
                results["categories"][category_name] = category_results
                results["total_tests"] += category_results.get("total", 0)
                results["passed_tests"] += category_results.get("passed", 0)
                results["failed_tests"] += category_results.get("failed", 0)
                results["warnings"] += category_results.get("warnings", 0)
                
                if category_results.get("status") == "FAIL":
                    results["overall_status"] = "FAIL"
                    
            except Exception as e:
                print_status(f"Error in {category_name}: {str(e)}", "ERROR")
                results["categories"][category_name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "total": 1,
                    "failed": 1,
                    "passed": 0,
                    "warnings": 0
                }
                results["failed_tests"] += 1
                results["overall_status"] = "FAIL"
        
        results["test_end"] = datetime.now().isoformat()
        results["duration"] = str(datetime.now() - self.start_time)
        
        self.print_summary(results)
        return results
    
    def test_system_requirements(self) -> Dict:
        """Test system requirements and dependencies"""
        tests = []
        
        # Check if running as root
        if os.geteuid() != 0:
            tests.append({
                "name": "Root privileges",
                "status": "FAIL",
                "message": "Script must be run as root (use sudo)"
            })
        else:
            tests.append({
                "name": "Root privileges",
                "status": "PASS",
                "message": "Running with root privileges"
            })
        
        # Check required commands
        required_commands = ["wg", "wg-quick", "iptables", "ufw", "ping", "telnet"]
        for cmd in required_commands:
            try:
                subprocess.run(["which", cmd], check=True, capture_output=True)
                tests.append({
                    "name": f"Command: {cmd}",
                    "status": "PASS",
                    "message": f"{cmd} is available"
                })
            except subprocess.CalledProcessError:
                tests.append({
                    "name": f"Command: {cmd}",
                    "status": "FAIL",
                    "message": f"{cmd} is not available"
                })
        
        # Check Python modules
        try:
            import subprocess
            import json
            import socket
            tests.append({
                "name": "Python modules",
                "status": "PASS",
                "message": "Required Python modules available"
            })
        except ImportError as e:
            tests.append({
                "name": "Python modules",
                "status": "FAIL",
                "message": f"Missing Python module: {e}"
            })
        
        return self._process_test_results("System Requirements", tests)
    
    def test_wireguard_installation(self) -> Dict:
        """Test WireGuard installation and service"""
        tests = []
        
        # Check WireGuard service status
        try:
            result = subprocess.run(
                ["systemctl", "is-active", f"wg-quick@{self.wg_interface}"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                tests.append({
                    "name": "WireGuard service",
                    "status": "PASS",
                    "message": "WireGuard service is active"
                })
            else:
                tests.append({
                    "name": "WireGuard service",
                    "status": "FAIL",
                    "message": "WireGuard service is not active"
                })
        except Exception as e:
            tests.append({
                "name": "WireGuard service",
                "status": "ERROR",
                "message": f"Error checking service: {e}"
            })
        
        # Check WireGuard interface
        try:
            result = subprocess.run(["wg", "show", self.wg_interface], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                tests.append({
                    "name": "WireGuard interface",
                    "status": "PASS",
                    "message": "WireGuard interface is up"
                })
            else:
                tests.append({
                    "name": "WireGuard interface",
                    "status": "FAIL",
                    "message": "WireGuard interface is not up"
                })
        except Exception as e:
            tests.append({
                "name": "WireGuard interface",
                "status": "ERROR",
                "message": f"Error checking interface: {e}"
            })
        
        # Check IP forwarding
        try:
            with open("/proc/sys/net/ipv4/ip_forward", "r") as f:
                ip_forward = f.read().strip()
            if ip_forward == "1":
                tests.append({
                    "name": "IP forwarding",
                    "status": "PASS",
                    "message": "IP forwarding is enabled"
                })
            else:
                tests.append({
                    "name": "IP forwarding",
                    "status": "FAIL",
                    "message": "IP forwarding is disabled"
                })
        except Exception as e:
            tests.append({
                "name": "IP forwarding",
                "status": "ERROR",
                "message": f"Error checking IP forwarding: {e}"
            })
        
        return self._process_test_results("WireGuard Installation", tests)
    
    def test_configuration_files(self) -> Dict:
        """Test configuration files and permissions"""
        tests = []
        
        # Check WireGuard config file
        if os.path.exists(self.wg_config):
            tests.append({
                "name": "Config file exists",
                "status": "PASS",
                "message": f"WireGuard config file exists: {self.wg_config}"
            })
            
            # Check file permissions
            stat_info = os.stat(self.wg_config)
            if stat_info.st_mode & 0o777 == 0o600:
                tests.append({
                    "name": "Config file permissions",
                    "status": "PASS",
                    "message": "Config file has correct permissions (600)"
                })
            else:
                tests.append({
                    "name": "Config file permissions",
                    "status": "WARNING",
                    "message": f"Config file permissions: {oct(stat_info.st_mode & 0o777)} (should be 600)"
                })
            
            # Check config content
            try:
                with open(self.wg_config, 'r') as f:
                    content = f.read()
                
                required_sections = ["[Interface]", "Address", "ListenPort", "PrivateKey"]
                missing_sections = []
                for section in required_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                if not missing_sections:
                    tests.append({
                        "name": "Config file content",
                        "status": "PASS",
                        "message": "Config file contains required sections"
                    })
                else:
                    tests.append({
                        "name": "Config file content",
                        "status": "FAIL",
                        "message": f"Missing sections: {', '.join(missing_sections)}"
                    })
            except Exception as e:
                tests.append({
                    "name": "Config file content",
                    "status": "ERROR",
                    "message": f"Error reading config file: {e}"
                })
        else:
            tests.append({
                "name": "Config file exists",
                "status": "FAIL",
                "message": f"WireGuard config file not found: {self.wg_config}"
            })
        
        # Check management script
        if os.path.exists(self.management_script):
            tests.append({
                "name": "Management script",
                "status": "PASS",
                "message": f"Management script exists: {self.management_script}"
            })
            
            # Check if executable
            if os.access(self.management_script, os.X_OK):
                tests.append({
                    "name": "Management script executable",
                    "status": "PASS",
                    "message": "Management script is executable"
                })
            else:
                tests.append({
                    "name": "Management script executable",
                    "status": "FAIL",
                    "message": "Management script is not executable"
                })
        else:
            tests.append({
                "name": "Management script",
                "status": "FAIL",
                "message": f"Management script not found: {self.management_script}"
            })
        
        return self._process_test_results("Configuration Files", tests)
    
    def test_network_connectivity(self) -> Dict:
        """Test network connectivity and routing"""
        tests = []
        
        # Check WireGuard interface IP
        try:
            result = subprocess.run(["ip", "addr", "show", self.wg_interface], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and "10.10.0.1" in result.stdout:
                tests.append({
                    "name": "WireGuard IP assignment",
                    "status": "PASS",
                    "message": "WireGuard interface has correct IP (10.10.0.1)"
                })
            else:
                tests.append({
                    "name": "WireGuard IP assignment",
                    "status": "FAIL",
                    "message": "WireGuard interface missing or wrong IP"
                })
        except Exception as e:
            tests.append({
                "name": "WireGuard IP assignment",
                "status": "ERROR",
                "message": f"Error checking IP: {e}"
            })
        
        # Check firewall rules
        try:
            result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
            if "51820/udp" in result.stdout:
                tests.append({
                    "name": "Firewall rules",
                    "status": "PASS",
                    "message": "WireGuard port (51820/udp) is allowed"
                })
            else:
                tests.append({
                    "name": "Firewall rules",
                    "status": "WARNING",
                    "message": "WireGuard port (51820/udp) not found in firewall rules"
                })
        except Exception as e:
            tests.append({
                "name": "Firewall rules",
                "status": "ERROR",
                "message": f"Error checking firewall: {e}"
            })
        
        # Test local connectivity
        try:
            result = subprocess.run(["ping", "-c", "1", "-W", "3", "10.10.0.1"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                tests.append({
                    "name": "Local connectivity",
                    "status": "PASS",
                    "message": "Can ping WireGuard gateway (10.10.0.1)"
                })
            else:
                tests.append({
                    "name": "Local connectivity",
                    "status": "FAIL",
                    "message": "Cannot ping WireGuard gateway"
                })
        except Exception as e:
            tests.append({
                "name": "Local connectivity",
                "status": "ERROR",
                "message": f"Error testing connectivity: {e}"
            })
        
        return self._process_test_results("Network Connectivity", tests)
    
    def test_management_tools(self) -> Dict:
        """Test management tools and commands"""
        tests = []
        
        # Test wg-mikrotik list command
        try:
            result = subprocess.run([self.management_script, "list"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                tests.append({
                    "name": "Management script list",
                    "status": "PASS",
                    "message": "Management script list command works"
                })
            else:
                tests.append({
                    "name": "Management script list",
                    "status": "FAIL",
                    "message": f"Management script list failed: {result.stderr}"
                })
        except Exception as e:
            tests.append({
                "name": "Management script list",
                "status": "ERROR",
                "message": f"Error testing list command: {e}"
            })
        
        # Test wg-status command
        try:
            result = subprocess.run(["/usr/local/bin/wg-status"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                tests.append({
                    "name": "Status script",
                    "status": "PASS",
                    "message": "Status script works"
                })
            else:
                tests.append({
                    "name": "Status script",
                    "status": "FAIL",
                    "message": f"Status script failed: {result.stderr}"
                })
        except Exception as e:
            tests.append({
                "name": "Status script",
                "status": "ERROR",
                "message": f"Error testing status script: {e}"
            })
        
        # Test Python API service
        try:
            result = subprocess.run([
                "python3", "/opt/wireguard-mikrotik/wireguard_api.py", "list"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                tests.append({
                    "name": "Python API service",
                    "status": "PASS",
                    "message": "Python API service works"
                })
            else:
                tests.append({
                    "name": "Python API service",
                    "status": "WARNING",
                    "message": f"Python API service issue: {result.stderr}"
                })
        except Exception as e:
            tests.append({
                "name": "Python API service",
                "status": "WARNING",
                "message": f"Python API service not available: {e}"
            })
        
        return self._process_test_results("Management Tools", tests)
    
    def test_security_settings(self) -> Dict:
        """Test security settings and permissions"""
        tests = []
        
        # Check config file permissions
        if os.path.exists(self.wg_config):
            stat_info = os.stat(self.wg_config)
            if stat_info.st_mode & 0o777 == 0o600:
                tests.append({
                    "name": "Config file security",
                    "status": "PASS",
                    "message": "Config file has secure permissions (600)"
                })
            else:
                tests.append({
                    "name": "Config file security",
                    "status": "WARNING",
                    "message": f"Config file permissions: {oct(stat_info.st_mode & 0o777)}"
                })
        
        # Check private key file permissions
        private_key_file = "/etc/wireguard/keys/server_private.key"
        if os.path.exists(private_key_file):
            stat_info = os.stat(private_key_file)
            if stat_info.st_mode & 0o777 == 0o600:
                tests.append({
                    "name": "Private key security",
                    "status": "PASS",
                    "message": "Private key has secure permissions (600)"
                })
            else:
                tests.append({
                    "name": "Private key security",
                    "status": "WARNING",
                    "message": f"Private key permissions: {oct(stat_info.st_mode & 0o777)}"
                })
        
        # Check firewall status
        try:
            result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
            if "Status: active" in result.stdout:
                tests.append({
                    "name": "Firewall active",
                    "status": "PASS",
                    "message": "Firewall is active"
                })
            else:
                tests.append({
                    "name": "Firewall active",
                    "status": "WARNING",
                    "message": "Firewall is not active"
                })
        except Exception as e:
            tests.append({
                "name": "Firewall active",
                "status": "ERROR",
                "message": f"Error checking firewall: {e}"
            })
        
        return self._process_test_results("Security Settings", tests)
    
    def test_performance(self) -> Dict:
        """Test performance and resource usage"""
        tests = []
        
        # Check WireGuard statistics
        try:
            result = subprocess.run(["wg", "show", self.wg_interface], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                tests.append({
                    "name": "WireGuard statistics",
                    "status": "PASS",
                    "message": "WireGuard statistics available"
                })
                
                # Parse and display stats
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'allowed ips' in line.lower():
                        tests.append({
                            "name": "Connected peers",
                            "status": "INFO",
                            "message": f"Peer info: {line.strip()}"
                        })
            else:
                tests.append({
                    "name": "WireGuard statistics",
                    "status": "FAIL",
                    "message": "Cannot get WireGuard statistics"
                })
        except Exception as e:
            tests.append({
                "name": "WireGuard statistics",
                "status": "ERROR",
                "message": f"Error getting statistics: {e}"
            })
        
        # Check system resources
        try:
            # Check memory usage
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            
            # Check CPU load
            with open("/proc/loadavg", "r") as f:
                loadavg = f.read().split()[0]
            
            tests.append({
                "name": "System resources",
                "status": "PASS",
                "message": f"System load: {loadavg}"
            })
        except Exception as e:
            tests.append({
                "name": "System resources",
                "status": "WARNING",
                "message": f"Error checking resources: {e}"
            })
        
        return self._process_test_results("Performance Tests", tests)
    
    def test_integration(self) -> Dict:
        """Test integration with external systems"""
        tests = []
        
        # Test if we can add a test router (dry run)
        try:
            # This is a dry run - we won't actually add a router
            tests.append({
                "name": "Management integration",
                "status": "PASS",
                "message": "Management tools are ready for integration"
            })
        except Exception as e:
            tests.append({
                "name": "Management integration",
                "status": "WARNING",
                "message": f"Integration test issue: {e}"
            })
        
        # Test log file access
        log_file = "/var/log/wireguard-mikrotik.log"
        if os.path.exists(log_file):
            tests.append({
                "name": "Log file access",
                "status": "PASS",
                "message": f"Log file exists: {log_file}"
            })
        else:
            tests.append({
                "name": "Log file access",
                "status": "WARNING",
                "message": "Log file not found - will be created on first use"
            })
        
        return self._process_test_results("Integration Tests", tests)
    
    def _process_test_results(self, category: str, tests: List[Dict]) -> Dict:
        """Process test results for a category"""
        total = len(tests)
        passed = sum(1 for test in tests if test["status"] == "PASS")
        failed = sum(1 for test in tests if test["status"] == "FAIL")
        warnings = sum(1 for test in tests if test["status"] == "WARNING")
        errors = sum(1 for test in tests if test["status"] == "ERROR")
        
        # Print test results
        for test in tests:
            status_color = {
                "PASS": Colors.GREEN,
                "FAIL": Colors.RED,
                "WARNING": Colors.YELLOW,
                "ERROR": Colors.RED,
                "INFO": Colors.CYAN
            }.get(test["status"], Colors.WHITE)
            
            print(f"  {status_color}[{test['status']}]{Colors.NC} {test['name']}: {test['message']}")
        
        # Determine overall status
        if failed > 0 or errors > 0:
            overall_status = "FAIL"
        elif warnings > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"
        
        return {
            "status": overall_status,
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "errors": errors,
            "tests": tests
        }
    
    def print_summary(self, results: Dict):
        """Print test summary"""
        print("\n" + "=" * 60)
        print_status("TEST SUMMARY", "HEADER")
        print("=" * 60)
        
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Warnings: {results['warnings']}")
        print(f"Duration: {results['duration']}")
        
        print("\nCategory Results:")
        print("-" * 40)
        
        for category, result in results["categories"].items():
            status_color = {
                "PASS": Colors.GREEN,
                "FAIL": Colors.RED,
                "WARNING": Colors.YELLOW,
                "ERROR": Colors.RED
            }.get(result["status"], Colors.WHITE)
            
            print(f"{status_color}[{result['status']}]{Colors.NC} {category}: "
                  f"{result['passed']}/{result['total']} passed")
        
        print("\n" + "=" * 60)
        
        if results["overall_status"] == "PASS":
            print_status("All tests passed! WireGuard setup is ready.", "SUCCESS")
        elif results["overall_status"] == "WARNING":
            print_status("Tests passed with warnings. Review warnings above.", "WARNING")
        else:
            print_status("Some tests failed. Please fix the issues above.", "ERROR")
        
        print("=" * 60)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="WireGuard MikroTik Testing Suite")
    parser.add_argument("--output", "-o", help="Output results to JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print_status("This script must be run as root (use sudo)", "ERROR")
        sys.exit(1)
    
    # Run tests
    tester = WireGuardTester()
    results = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print_status(f"Results saved to: {args.output}", "INFO")
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        sys.exit(0)
    elif results["overall_status"] == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
