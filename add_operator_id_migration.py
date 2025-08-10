#!/usr/bin/env python3
"""
Migration script to add sportsbook_operator_id to existing users and bets tables
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = 'src/database/app.db'

def add_operator_id_columns():
    """Add sportsbook_operator_id columns to users and bets tables"""
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("🔄 Adding sportsbook_operator_id columns...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(bets)")
        bet_columns = [column[1] for column in cursor.fetchall()]
        
        # Add sportsbook_operator_id to users table if it doesn't exist
        if 'sportsbook_operator_id' not in user_columns:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN sportsbook_operator_id INTEGER
            """)
            print("✅ Added sportsbook_operator_id column to users table")
        else:
            print("ℹ️  sportsbook_operator_id column already exists in users table")
        
        # Add sportsbook_operator_id to bets table if it doesn't exist
        if 'sportsbook_operator_id' not in bet_columns:
            cursor.execute("""
                ALTER TABLE bets 
                ADD COLUMN sportsbook_operator_id INTEGER
            """)
            print("✅ Added sportsbook_operator_id column to bets table")
        else:
            print("ℹ️  sportsbook_operator_id column already exists in bets table")
        
        # Get the default operator (first one created)
        cursor.execute("SELECT id FROM sportsbook_operators ORDER BY id LIMIT 1")
        default_operator = cursor.fetchone()
        
        if default_operator:
            default_operator_id = default_operator[0]
            
            # Update existing users to belong to the default operator
            cursor.execute("""
                UPDATE users 
                SET sportsbook_operator_id = ? 
                WHERE sportsbook_operator_id IS NULL
            """, (default_operator_id,))
            
            updated_users = cursor.rowcount
            print(f"✅ Updated {updated_users} existing users to belong to default operator (ID: {default_operator_id})")
            
            # Update existing bets to belong to the default operator
            cursor.execute("""
                UPDATE bets 
                SET sportsbook_operator_id = ? 
                WHERE sportsbook_operator_id IS NULL
            """, (default_operator_id,))
            
            updated_bets = cursor.rowcount
            print(f"✅ Updated {updated_bets} existing bets to belong to default operator (ID: {default_operator_id})")
            
        else:
            print("⚠️  No sportsbook operators found. Existing users and bets will remain unassigned.")
        
        conn.commit()
        conn.close()
        
        print("🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """Verify the migration was successful"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("\n🔍 Verifying migration...")
        
        # Check users table structure
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        if 'sportsbook_operator_id' in user_columns:
            print("✅ Users table has sportsbook_operator_id column")
            
            # Count users by operator
            cursor.execute("""
                SELECT 
                    sportsbook_operator_id,
                    COUNT(*) as user_count
                FROM users 
                GROUP BY sportsbook_operator_id
            """)
            
            user_counts = cursor.fetchall()
            for operator_id, count in user_counts:
                if operator_id:
                    cursor.execute("SELECT sportsbook_name FROM sportsbook_operators WHERE id = ?", (operator_id,))
                    operator_name = cursor.fetchone()
                    operator_name = operator_name[0] if operator_name else f"Operator {operator_id}"
                    print(f"   - {operator_name}: {count} users")
                else:
                    print(f"   - Unassigned: {count} users")
        else:
            print("❌ Users table missing sportsbook_operator_id column")
        
        # Check bets table structure
        cursor.execute("PRAGMA table_info(bets)")
        bet_columns = [column[1] for column in cursor.fetchall()]
        
        if 'sportsbook_operator_id' in bet_columns:
            print("✅ Bets table has sportsbook_operator_id column")
            
            # Count bets by operator
            cursor.execute("""
                SELECT 
                    sportsbook_operator_id,
                    COUNT(*) as bet_count
                FROM bets 
                GROUP BY sportsbook_operator_id
            """)
            
            bet_counts = cursor.fetchall()
            for operator_id, count in bet_counts:
                if operator_id:
                    cursor.execute("SELECT sportsbook_name FROM sportsbook_operators WHERE id = ?", (operator_id,))
                    operator_name = cursor.fetchone()
                    operator_name = operator_name[0] if operator_name else f"Operator {operator_id}"
                    print(f"   - {operator_name}: {count} bets")
                else:
                    print(f"   - Unassigned: {count} bets")
        else:
            print("❌ Bets table missing sportsbook_operator_id column")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")

def main():
    """Main function"""
    print("🔧 GoalServe Multi-Tenant Migration")
    print("=" * 50)
    print("Adding sportsbook_operator_id columns to existing tables...")
    
    success = add_operator_id_columns()
    
    if success:
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        print("Users and bets are now properly associated with sportsbook operators.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")

if __name__ == "__main__":
    main()

