#!/bin/bash

# WireGuard MikroTik VPS Supabase Setup Script
# This script sets up Supabase integration for the WireGuard management system

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

print_status "Setting up Supabase integration for WireGuard MikroTik VPS..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Install Supabase Python client
print_status "Installing Supabase Python client..."
pip3 install supabase

# Create config directory
print_status "Creating configuration directory..."
mkdir -p /opt/wireguard-mikrotik-vps/config

# Create Supabase configuration file
print_status "Creating Supabase configuration file..."
cat > /opt/wireguard-mikrotik-vps/config/supabase.json << 'EOF'
{
  "url": "",
  "key": "",
  "table": "routers"
}
EOF

print_warning "Please configure your Supabase credentials:"
echo "1. Edit /opt/wireguard-mikrotik-vps/config/supabase.json"
echo "2. Add your Supabase URL and API key"
echo "3. Or set environment variables:"
echo "   export SUPABASE_URL='https://your-project.supabase.co'"
echo "   export SUPABASE_KEY='your-supabase-anon-key'"

# Create database schema SQL
print_status "Creating database schema..."
cat > /opt/wireguard-mikrotik-vps/config/database_schema.sql << 'EOF'
-- WireGuard MikroTik VPS Database Schema
-- Run this in your Supabase SQL editor

-- Create routers table
CREATE TABLE IF NOT EXISTS routers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    public_key TEXT NOT NULL UNIQUE,
    ip_address VARCHAR(15),
    vpn_type VARCHAR(20) DEFAULT 'wireguard',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_vpn_check TIMESTAMP WITH TIME ZONE,
    api_accessible BOOLEAN DEFAULT false,
    notes TEXT
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_routers_vpn_type ON routers(vpn_type);
CREATE INDEX IF NOT EXISTS idx_routers_is_active ON routers(is_active);
CREATE INDEX IF NOT EXISTS idx_routers_public_key ON routers(public_key);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_routers_updated_at ON routers;
CREATE TRIGGER update_routers_updated_at
    BEFORE UPDATE ON routers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
INSERT INTO routers (name, public_key, ip_address, vpn_type, is_active) VALUES
('Sample Router 1', 'sample_public_key_1', '10.10.0.2', 'wireguard', true),
('Sample Router 2', 'sample_public_key_2', '10.10.0.3', 'wireguard', true)
ON CONFLICT (name) DO NOTHING;
EOF

print_success "Supabase integration setup completed!"
print_status "Next steps:"
echo "1. Configure your Supabase credentials in /opt/wireguard-mikrotik-vps/config/supabase.json"
echo "2. Run the SQL schema in your Supabase SQL editor:"
echo "   cat /opt/wireguard-mikrotik-vps/config/database_schema.sql"
echo "3. Test the integration by running: wg-menu"
echo ""
print_status "The menu system will now work with:"
echo "  ✓ Local WireGuard configuration"
echo "  ✓ Supabase database (when configured)"
echo "  ✓ Django database (if available)"
