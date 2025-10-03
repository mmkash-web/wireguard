#!/usr/bin/env python3
"""
Test Database Connection for WireGuard MikroTik VPS
Tests the database connection using the same credentials as main Django system
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager

def test_database_connection():
    """Test database connection and basic operations"""
    print("=" * 60)
    print("WireGuard MikroTik VPS - Database Connection Test")
    print("=" * 60)
    
    # Test database connection
    print("\n1. Testing database connection...")
    db = DatabaseManager()
    
    if not db.available:
        print("❌ Database connection failed!")
        print("   Make sure psycopg2-binary is installed:")
        print("   pip install psycopg2-binary")
        return False
    
    print("✅ Database connection successful!")
    
    # Test basic operations
    print("\n2. Testing database operations...")
    
    # Test getting routers
    print("   - Getting routers...")
    routers = db.get_routers()
    print(f"   ✅ Found {len(routers)} routers in database")
    
    # Test adding a test router
    print("   - Adding test router...")
    test_router = {
        'name': 'test-vps-router',
        'public_key': 'test-public-key-12345',
        'ip_address': '10.10.0.100',
        'vpn_type': 'wireguard',
        'is_active': True,
        'api_accessible': False,
        'notes': 'Test router from VPS database test'
    }
    
    if db.add_router(test_router):
        print("   ✅ Test router added successfully")
        
        # Test getting the router back
        print("   - Retrieving test router...")
        retrieved_router = db.get_router_by_name('test-vps-router')
        if retrieved_router:
            print("   ✅ Test router retrieved successfully")
            print(f"      Name: {retrieved_router.get('name')}")
            print(f"      IP: {retrieved_router.get('ip_address')}")
            print(f"      Active: {retrieved_router.get('is_active')}")
        else:
            print("   ❌ Failed to retrieve test router")
        
        # Clean up test router
        print("   - Cleaning up test router...")
        if retrieved_router and 'id' in retrieved_router:
            if db.delete_router(retrieved_router['id']):
                print("   ✅ Test router deleted successfully")
            else:
                print("   ⚠️  Failed to delete test router")
    else:
        print("   ❌ Failed to add test router")
    
    # Test connection
    print("\n3. Testing connection stability...")
    if db.test_connection():
        print("   ✅ Database connection is stable")
    else:
        print("   ❌ Database connection test failed")
    
    # Close connection
    db.close()
    print("\n4. Database connection closed")
    
    print("\n" + "=" * 60)
    print("Database test completed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_database_connection()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
