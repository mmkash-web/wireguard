#!/usr/bin/env python3
"""
Database Manager for WireGuard MikroTik VPS
Uses the same approach as the main Django system with Supabase PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
import json

class DatabaseManager:
    """Manages database connections using the same approach as main Django system"""
    
    def __init__(self):
        self.connection = None
        self.available = False
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection using same credentials as main Django system"""
        try:
            # Use the same credentials as your main Django system
            db_config = {
                'host': 'aws-1-eu-west-2.pooler.supabase.com',
                'port': '5432',
                'database': 'postgres',
                'user': 'postgres.seuzxvthbxowmofxalmm',
                'password': 'Emmkash20'
            }
            
            # Try to connect
            self.connection = psycopg2.connect(**db_config)
            self.available = True
            print("✓ Database connection established")
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.available = False
    
    def get_routers(self) -> List[Dict]:
        """Get routers from database using same table structure as Django"""
        if not self.available:
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        id,
                        name,
                        public_key,
                        ip_address,
                        vpn_type,
                        is_active,
                        created_at,
                        updated_at,
                        last_vpn_check,
                        api_accessible,
                        notes
                    FROM routers 
                    WHERE vpn_type = 'wireguard'
                    ORDER BY created_at DESC
                """)
                
                routers = cursor.fetchall()
                return [dict(router) for router in routers]
                
        except Exception as e:
            print(f"Error fetching routers from database: {e}")
            return []
    
    def add_router(self, router_data: Dict) -> bool:
        """Add router to database"""
        if not self.available:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO routers (
                        name, public_key, ip_address, vpn_type, 
                        is_active, api_accessible, notes
                    ) VALUES (
                        %(name)s, %(public_key)s, %(ip_address)s, %(vpn_type)s,
                        %(is_active)s, %(api_accessible)s, %(notes)s
                    )
                    ON CONFLICT (name) DO UPDATE SET
                        public_key = EXCLUDED.public_key,
                        ip_address = EXCLUDED.ip_address,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                """, router_data)
                
                self.connection.commit()
                return True
                
        except Exception as e:
            print(f"Error adding router to database: {e}")
            return False
    
    def update_router(self, router_id: int, updates: Dict) -> bool:
        """Update router in database"""
        if not self.available:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                set_clauses = []
                values = {'id': router_id}
                
                for key, value in updates.items():
                    set_clauses.append(f"{key} = %({key})s")
                    values[key] = value
                
                if set_clauses:
                    query = f"""
                        UPDATE routers 
                        SET {', '.join(set_clauses)}, updated_at = NOW()
                        WHERE id = %(id)s
                    """
                    cursor.execute(query, values)
                    self.connection.commit()
                    return True
                    
        except Exception as e:
            print(f"Error updating router in database: {e}")
            return False
    
    def delete_router(self, router_id: int) -> bool:
        """Delete router from database"""
        if not self.available:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM routers WHERE id = %s", (router_id,))
                self.connection.commit()
                return True
                
        except Exception as e:
            print(f"Error deleting router from database: {e}")
            return False
    
    def get_router_by_name(self, name: str) -> Optional[Dict]:
        """Get router by name"""
        if not self.available:
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM routers 
                    WHERE name = %s AND vpn_type = 'wireguard'
                """, (name,))
                
                router = cursor.fetchone()
                return dict(router) if router else None
                
        except Exception as e:
            print(f"Error fetching router by name: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test database connection"""
        if not self.available:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.available = False

# Database credentials are hardcoded to match main Django system
DATABASE_CONFIG = {
    'host': 'aws-1-eu-west-2.pooler.supabase.com',
    'port': '5432',
    'database': 'postgres',
    'user': 'postgres.seuzxvthbxowmofxalmm',
    'password': 'Emmkash20'
}

if __name__ == "__main__":
    # Test database connection
    db = DatabaseManager()
    if db.available:
        print("✓ Database connection successful!")
        
        # Test getting routers
        routers = db.get_routers()
        print(f"Found {len(routers)} routers in database")
        
        # Test adding a router
        test_router = {
            'name': 'test-router',
            'public_key': 'test-public-key',
            'ip_address': '10.10.0.100',
            'vpn_type': 'wireguard',
            'is_active': True,
            'api_accessible': False,
            'notes': 'Test router from VPS'
        }
        
        if db.add_router(test_router):
            print("✓ Test router added successfully")
        else:
            print("✗ Failed to add test router")
        
        db.close()
    else:
        print("✗ Database connection failed")
