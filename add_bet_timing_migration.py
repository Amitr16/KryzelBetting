#!/usr/bin/env python3
"""
Database Migration: Add bet_timing column to bets table
This distinguishes between pregame and ingame bets
"""

import sqlite3
import os
import sys

def run_migration():
    """Add bet_timing column to bets table"""
    try:
        # Database path
        db_path = os.path.join('src', 'database', 'app.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"🔧 Running bet_timing migration on: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if bet_timing column already exists
        cursor.execute("PRAGMA table_info(bets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'bet_timing' in columns:
            print("✅ bet_timing column already exists")
            conn.close()
            return True
        
        # Add bet_timing column
        print("➕ Adding bet_timing column to bets table...")
        cursor.execute("""
            ALTER TABLE bets 
            ADD COLUMN bet_timing VARCHAR(20) DEFAULT 'pregame'
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(bets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'bet_timing' in columns:
            print("✅ bet_timing column added successfully")
            
            # Show updated table structure
            cursor.execute("PRAGMA table_info(bets)")
            print("\n📋 Updated bets table structure:")
            for column in cursor.fetchall():
                print(f"  - {column[1]} ({column[2]})")
            
            conn.close()
            return True
        else:
            print("❌ Failed to add bet_timing column")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def set_all_existing_bets_as_pregame():
    """Set all existing bets as pregame since current functionality is pregame only"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Setting all existing bets as pregame...")
        
        # Get all bets (should all be pregame since no ingame functionality yet)
        cursor.execute("""
            SELECT id, match_id, match_name, created_at 
            FROM bets 
            WHERE bet_timing IS NULL OR bet_timing = 'pregame'
        """)
        
        bets = cursor.fetchall()
        print(f"📊 Found {len(bets)} bets to set as pregame")
        
        updated_count = 0
        
        for bet_id, match_id, match_name, created_at in bets:
            # Set all existing bets as pregame (current functionality)
            bet_timing = 'pregame'
            
            cursor.execute("""
                UPDATE bets 
                SET bet_timing = ? 
                WHERE id = ?
            """, (bet_timing, bet_id))
            updated_count += 1
            print(f"  ✅ Bet {bet_id}: {match_name} → {bet_timing}")
        
        conn.commit()
        print(f"✅ Updated {updated_count} bets as pregame")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to update bet_timing: {e}")
        return False

def show_current_status():
    """Show current bet_timing status"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 CURRENT BET TIMING STATUS:")
        print("=" * 50)
        
        # Count bets by timing
        cursor.execute("""
            SELECT bet_timing, COUNT(*) as count
            FROM bets 
            GROUP BY bet_timing
        """)
        
        results = cursor.fetchall()
        for timing, count in results:
            print(f"  {timing or 'NULL'}: {count} bets")
        
        # Show sample bets
        cursor.execute("""
            SELECT id, match_name, bet_timing, created_at
            FROM bets 
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        print(f"\n📋 Sample bets:")
        for bet_id, match_name, bet_timing, created_at in cursor.fetchall():
            print(f"  Bet {bet_id}: {match_name} → {bet_timing or 'NULL'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to show status: {e}")
        return False

def show_future_implementation():
    """Show how ingame betting will be implemented"""
    print("\n🔮 FUTURE INGAME IMPLEMENTATION:")
    print("=" * 50)
    print("""
    When you implement ingame betting:
    
    1. Add ingame odds endpoints:
       - /api/odds/ingame/{sport}
       - Real-time odds during matches
    
    2. Update betting routes:
       - Check match status at betting time
       - Set bet_timing = 'ingame' for live matches
       - Set bet_timing = 'pregame' for future matches
    
    3. Different settlement rules:
       - Pregame: Settle at match end
       - Ingame: May have different rules
    
    4. Analytics:
       - Track pregame vs ingame betting patterns
       - Different risk management
    """)

if __name__ == "__main__":
    print("🚀 Starting bet_timing migration...")
    print("=" * 50)
    
    # Run migration
    if run_migration():
        print("\n🔄 Setting existing bets as pregame...")
        set_all_existing_bets_as_pregame()
        
        print("\n📊 Checking current status...")
        show_current_status()
        
        print("\n✅ Migration completed successfully!")
        print("\n📝 Summary:")
        print("  - bet_timing column added to bets table")
        print("  - All existing bets set as 'pregame'")
        print("  - Default for new bets is 'pregame'")
        print("  - Ready for future ingame implementation")
        
        show_future_implementation()
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
