# Database Integration - WireGuard MikroTik VPS

## 🎯 **Overview**

The WireGuard MikroTik VPS system now integrates with the same Supabase PostgreSQL database as your main Django system. This provides:

- **Unified Data Storage** - Same database as main system
- **Real-time Sync** - Changes reflect across all systems
- **Persistent Storage** - Data survives VPS reboots
- **Backup & Recovery** - Data backed up with main system

## 🔧 **Database Configuration**

### **Credentials (Same as Main System)**
```
Host: aws-1-eu-west-2.pooler.supabase.com
Port: 5432
Database: postgres
User: postgres.seuzxvthbxowmofxalmm
Password: Emmkash20
```

### **Table Structure**
Uses the same `routers` table as your main Django system:
- `id` - Primary key
- `name` - Router name
- `public_key` - WireGuard public key
- `ip_address` - VPN IP address
- `vpn_type` - Always 'wireguard'
- `is_active` - Router status
- `api_accessible` - API connectivity
- `notes` - Additional notes
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## 🚀 **Setup Process**

### **Automatic Setup (Recommended)**
```bash
# Run the main installer (includes database setup)
sudo bash /opt/wireguard-mikrotik-vps/install.sh
```

### **Manual Setup**
```bash
# Install database dependencies
sudo bash /opt/wireguard-mikrotik-vps/setup-database.sh

# Test database connection
python3 /opt/wireguard-mikrotik-vps/test-database.py
```

## 📊 **Data Sources Priority**

The system checks data sources in this order:

1. **Database (Primary)** - Same as main Django system
2. **Django Database** - If Django is available
3. **Supabase API** - If Supabase is configured
4. **WireGuard Config** - Local configuration file

## 🔄 **How It Works**

### **Adding Routers**
1. Router added to WireGuard configuration
2. Router data saved to database
3. Changes sync with main Django system
4. Data persists across reboots

### **Listing Routers**
1. Fetches from database first (primary source)
2. Falls back to other sources if needed
3. Shows data source for each router
4. Displays unified view

### **Data Synchronization**
- **Real-time** - Changes appear immediately
- **Bidirectional** - VPS ↔ Main System
- **Persistent** - Survives reboots and restarts
- **Consistent** - Same data across all systems

## 🛠️ **Management Commands**

### **Menu System**
```bash
# Access main menu (with database integration)
wg-menu

# View dashboard
wg-dashboard

# Check status
wg-status
```

### **Database Operations**
```bash
# Test database connection
python3 /opt/wireguard-mikrotik-vps/test-database.py

# Check database status
python3 -c "from database_manager import DatabaseManager; db = DatabaseManager(); print('Available:', db.available)"
```

## 🔍 **Troubleshooting**

### **Database Connection Issues**
```bash
# Check if psycopg2 is installed
python3 -c "import psycopg2; print('psycopg2 available')"

# Test connection manually
python3 /opt/wireguard-mikrotik-vps/test-database.py

# Check network connectivity
ping aws-1-eu-west-2.pooler.supabase.com
```

### **Common Issues**
1. **Missing psycopg2** - Run `pip3 install psycopg2-binary`
2. **Network issues** - Check VPS internet connection
3. **Credentials** - Verify database credentials are correct
4. **Firewall** - Ensure port 5432 is not blocked

## 📈 **Benefits**

### **For VPS Management**
- ✅ **Persistent Data** - Router info survives reboots
- ✅ **Real-time Sync** - Changes reflect immediately
- ✅ **Unified View** - Same data as main system
- ✅ **Backup Protection** - Data backed up with main system

### **For Main System**
- ✅ **VPS Integration** - VPS changes appear in main system
- ✅ **Unified Management** - Manage from both systems
- ✅ **Data Consistency** - Single source of truth
- ✅ **Scalability** - Easy to add more VPS instances

## 🎉 **Result**

Your WireGuard MikroTik VPS now has **full database integration** with your main Django system:

- **Same Database** - Uses identical credentials and table structure
- **Real-time Sync** - Changes appear across all systems
- **Persistent Storage** - Data survives VPS reboots
- **Unified Management** - Manage routers from anywhere
- **Backup Protection** - Data backed up with main system

The VPS is now a **fully integrated part** of your MikroTik billing system! 🚀
