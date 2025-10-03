#!/bin/bash

# WireGuard MikroTik VPS Database Setup
# Sets up database connection using same credentials as main Django system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "Setting up database connection for WireGuard MikroTik VPS..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Install PostgreSQL client libraries
print_status "Installing PostgreSQL client libraries..."
apt-get update
apt-get install -y postgresql-client libpq-dev python3-dev

# Install Python database dependencies
print_status "Installing Python database dependencies..."
pip3 install psycopg2-binary

# Test database connection
print_status "Testing database connection..."
cd /opt/wireguard-mikrotik-vps
python3 test-database.py

if [ $? -eq 0 ]; then
    print_success "Database setup completed successfully!"
    print_status "Your VPS can now connect to the same database as your main Django system"
    print_status "Database credentials:"
    echo "  Host: aws-1-eu-west-2.pooler.supabase.com"
    echo "  Port: 5432"
    echo "  Database: postgres"
    echo "  User: postgres.seuzxvthbxowmofxalmm"
    echo "  Password: Emmkash20"
else
    print_error "Database setup failed!"
    print_warning "Please check the error messages above and try again"
    exit 1
fi

print_status "You can now use the menu system with full database integration:"
echo "  wg-menu"
echo "  wg-dashboard"
echo "  wg-status"
