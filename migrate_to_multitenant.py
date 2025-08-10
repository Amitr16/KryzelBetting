#!/usr/bin/env python3
"""
Database Migration Script for Multi-Tenant Support
This script migrates the existing GoalServe database to support multi-tenant architecture
"""

import sqlite3
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Database path
DATABASE_PATH = 'src/database/app.db'

def backup_database():
    """Create a backup of the current database"""
    backup_path = f"src/database/app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # Copy the database file
    import shutil
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path

def create_new_tables(conn):
    """Create new tables for multi-tenant support"""
    cursor = conn.cursor()
    
    # Create sportsbook_operators table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sportsbook_operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sportsbook_name VARCHAR(100) NOT NULL UNIQUE,
            login VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(120),
            subdomain VARCHAR(50) NOT NULL UNIQUE,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            total_revenue FLOAT DEFAULT 0.0,
            commission_rate FLOAT DEFAULT 0.05,
            settings TEXT
        )
    """)
    
    # Create super_admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS super_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            permissions TEXT
        )
    """)
    
    print("✅ New tables created successfully")

def add_foreign_key_columns(conn):
    """Add sportsbook_operator_id columns to existing tables"""
    cursor = conn.cursor()
    
    # Check if columns already exist
    tables_to_modify = ['users', 'bets', 'transactions', 'bet_slips']
    
    for table in tables_to_modify:
        try:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'sportsbook_operator_id' not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN sportsbook_operator_id INTEGER")
                print(f"✅ Added sportsbook_operator_id column to {table} table")
            else:
                print(f"ℹ️  Column sportsbook_operator_id already exists in {table} table")
                
        except sqlite3.Error as e:
            print(f"❌ Error modifying {table} table: {e}")

def create_indexes(conn):
    """Create indexes for better performance"""
    cursor = conn.cursor()
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_sportsbook_operator ON users(sportsbook_operator_id)",
        "CREATE INDEX IF NOT EXISTS idx_bets_sportsbook_operator ON bets(sportsbook_operator_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_sportsbook_operator ON transactions(sportsbook_operator_id)",
        "CREATE INDEX IF NOT EXISTS idx_bet_slips_sportsbook_operator ON bet_slips(sportsbook_operator_id)",
        "CREATE INDEX IF NOT EXISTS idx_sportsbook_operators_subdomain ON sportsbook_operators(subdomain)",
        "CREATE INDEX IF NOT EXISTS idx_sportsbook_operators_login ON sportsbook_operators(login)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except sqlite3.Error as e:
            print(f"❌ Error creating index: {e}")
    
    print("✅ Indexes created successfully")

def create_default_data(conn):
    """Create default super admin and sportsbook operator"""
    cursor = conn.cursor()
    
    # Create default super admin
    super_admin_password = generate_password_hash('superadmin123')
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO super_admins (username, password_hash, email, permissions)
            VALUES (?, ?, ?, ?)
        """, ('superadmin', super_admin_password, 'superadmin@goalserve.com', '{"all": true}'))
        print("✅ Default super admin created (username: superadmin, password: superadmin123)")
    except sqlite3.Error as e:
        print(f"ℹ️  Super admin might already exist: {e}")
    
    # Create default sportsbook operator for existing data
    default_admin_password = generate_password_hash('admin123')
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO sportsbook_operators 
            (sportsbook_name, login, password_hash, subdomain, email, settings)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Default Sportsbook', 'admin', default_admin_password, 'default', 
              'admin@default.com', '{"theme": "default", "currency": "USD"}'))
        
        # Get the default operator ID
        cursor.execute("SELECT id FROM sportsbook_operators WHERE subdomain = 'default'")
        default_operator_id = cursor.fetchone()[0]
        
        print(f"✅ Default sportsbook operator created (login: admin, password: admin123)")
        return default_operator_id
        
    except sqlite3.Error as e:
        print(f"ℹ️  Default operator might already exist: {e}")
        cursor.execute("SELECT id FROM sportsbook_operators WHERE subdomain = 'default'")
        result = cursor.fetchone()
        return result[0] if result else None

def migrate_existing_data(conn, default_operator_id):
    """Associate existing data with default operator"""
    if not default_operator_id:
        print("❌ Cannot migrate existing data - no default operator ID")
        return
    
    cursor = conn.cursor()
    
    # Update existing users
    cursor.execute("""
        UPDATE users 
        SET sportsbook_operator_id = ? 
        WHERE sportsbook_operator_id IS NULL
    """, (default_operator_id,))
    users_updated = cursor.rowcount
    
    # Update existing bets
    cursor.execute("""
        UPDATE bets 
        SET sportsbook_operator_id = ? 
        WHERE sportsbook_operator_id IS NULL
    """, (default_operator_id,))
    bets_updated = cursor.rowcount
    
    # Update existing transactions
    cursor.execute("""
        UPDATE transactions 
        SET sportsbook_operator_id = ? 
        WHERE sportsbook_operator_id IS NULL
    """, (default_operator_id,))
    transactions_updated = cursor.rowcount
    
    # Update existing bet_slips
    cursor.execute("""
        UPDATE bet_slips 
        SET sportsbook_operator_id = ? 
        WHERE sportsbook_operator_id IS NULL
    """, (default_operator_id,))
    bet_slips_updated = cursor.rowcount
    
    print(f"✅ Migrated existing data:")
    print(f"   - Users: {users_updated}")
    print(f"   - Bets: {bets_updated}")
    print(f"   - Transactions: {transactions_updated}")
    print(f"   - Bet Slips: {bet_slips_updated}")

def verify_migration(conn):
    """Verify the migration was successful"""
    cursor = conn.cursor()
    
    # Check table existence
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['sportsbook_operators', 'super_admins']
    for table in required_tables:
        if table in tables:
            print(f"✅ Table {table} exists")
        else:
            print(f"❌ Table {table} missing")
    
    # Check data counts
    cursor.execute("SELECT COUNT(*) FROM sportsbook_operators")
    operators_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM super_admins")
    super_admins_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE sportsbook_operator_id IS NOT NULL")
    users_with_operator = cursor.fetchone()[0]
    
    print(f"✅ Migration verification:")
    print(f"   - Sportsbook operators: {operators_count}")
    print(f"   - Super admins: {super_admins_count}")
    print(f"   - Users with operator association: {users_with_operator}")

def main():
    """Main migration function"""
    print("🚀 Starting Multi-Tenant Database Migration")
    print("=" * 50)
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at: {DATABASE_PATH}")
        sys.exit(1)
    
    # Create backup
    backup_path = backup_database()
    
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
        # Run migration steps
        create_new_tables(conn)
        add_foreign_key_columns(conn)
        create_indexes(conn)
        default_operator_id = create_default_data(conn)
        migrate_existing_data(conn, default_operator_id)
        
        # Commit changes
        conn.commit()
        
        # Verify migration
        verify_migration(conn)
        
        print("\n" + "=" * 50)
        print("✅ Migration completed successfully!")
        print("\nDefault Credentials:")
        print("Super Admin - username: superadmin, password: superadmin123")
        print("Default Operator - login: admin, password: admin123")
        print(f"\nBackup created at: {backup_path}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"Database backup available at: {backup_path}")
        sys.exit(1)
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()

