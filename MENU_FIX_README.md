# WireGuard MikroTik VPS Menu Fix

## 🚨 Problem Fixed

The menu system was showing "❌ Django not available. Cannot list routers from database." because it was trying to use Django database integration that wasn't available.

## ✅ Solution Implemented

The menu system now works with **multiple data sources**:

1. **WireGuard Configuration** (Always available)
2. **Supabase Database** (Optional)
3. **Django Database** (Optional)

## 🔧 What Was Fixed

### 1. **WireGuardConfigManager Class**
- Reads routers directly from `/etc/wireguard/wg0.conf`
- Manages peer additions/removals
- Auto-assigns IP addresses
- No database dependency

### 2. **SupabaseManager Class**
- Optional Supabase integration
- Reads from environment variables or config file
- Graceful fallback if not configured

### 3. **Updated Menu Functions**
- `list_routers()` - Now works with all data sources
- `add_router()` - Adds to WireGuard config + optional databases
- Shows data source for each router

## 🚀 How to Use

### Quick Fix (Run This)
```bash
sudo bash /opt/wireguard-mikrotik-vps/fix-menu.sh
```

### Manual Setup

1. **Install Supabase (Optional)**
```bash
pip3 install supabase
```

2. **Configure Supabase (Optional)**
```bash
# Edit config file
nano /opt/wireguard-mikrotik-vps/config/supabase.json

# Or set environment variables
export SUPABASE_URL='https://your-project.supabase.co'
export SUPABASE_KEY='your-supabase-anon-key'
```

3. **Run the Menu**
```bash
wg-menu
```

## 📊 Data Sources

The menu now shows which data source each router comes from:

| Name | VPN IP | Status | Source | Public Key |
|------|--------|--------|--------|------------|
| Router1 | 10.10.0.2 | Active | WireGuard Config | abc123... |
| Router2 | 10.10.0.3 | Active | Supabase | def456... |
| Router3 | 10.10.0.4 | Active | Django DB | ghi789... |

## 🔧 Configuration Files

### Supabase Configuration
```json
{
  "url": "https://your-project.supabase.co",
  "key": "your-supabase-anon-key",
  "table": "routers"
}
```

### Environment Variables
```bash
export SUPABASE_URL='https://your-project.supabase.co'
export SUPABASE_KEY='your-supabase-anon-key'
```

## 🎯 Features

### ✅ Always Works
- Lists routers from WireGuard configuration
- Adds/removes routers
- Auto-assigns IP addresses
- No external dependencies

### ✅ Optional Integrations
- **Supabase**: Cloud database integration
- **Django**: Local database integration
- **Multiple sources**: Combines data from all sources

### ✅ Smart Fallbacks
- If Supabase fails → Uses WireGuard config
- If Django fails → Uses WireGuard config
- Always shows what data sources are available

## 🛠️ Troubleshooting

### Menu Shows "No Routers Found"
```bash
# Check WireGuard status
wg show

# Check config file
cat /etc/wireguard/wg0.conf

# Add a test router
wg-mikrotik add test-router sample_public_key
```

### Supabase Integration Not Working
```bash
# Check configuration
cat /opt/wireguard-mikrotik-vps/config/supabase.json

# Test connection
python3 -c "
from supabase import create_client
client = create_client('your-url', 'your-key')
print('Supabase connection successful!')
"
```

### Menu Crashes
```bash
# Run the fix script
sudo bash /opt/wireguard-mikrotik-vps/fix-menu.sh

# Check for errors
python3 /opt/wireguard-mikrotik-vps/menu/wireguard-menu.py
```

## 📋 Database Schema (Supabase)

If using Supabase, create this table:

```sql
CREATE TABLE routers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    public_key TEXT NOT NULL UNIQUE,
    ip_address VARCHAR(15),
    vpn_type VARCHAR(20) DEFAULT 'wireguard',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🎉 Result

The menu system now works perfectly without Django and provides a robust, multi-source router management system that gracefully handles missing dependencies while providing optional database integrations.

**No more "Django not available" errors!** 🚀
