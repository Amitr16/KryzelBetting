#!/usr/bin/env python3
"""
Database Migration: Add sport_name column to bets table
This makes settlement more reliable by storing sport at betting time
"""

import sqlite3
import os
import sys

def run_migration():
    """Add sport_name column to bets table"""
    try:
        # Database path
        db_path = os.path.join('src', 'database', 'app.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"🔧 Running migration on: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if sport_name column already exists
        cursor.execute("PRAGMA table_info(bets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sport_name' in columns:
            print("✅ sport_name column already exists")
            conn.close()
            return True
        
        # Add sport_name column
        print("➕ Adding sport_name column to bets table...")
        cursor.execute("""
            ALTER TABLE bets 
            ADD COLUMN sport_name VARCHAR(50)
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(bets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sport_name' in columns:
            print("✅ sport_name column added successfully")
            
            # Show updated table structure
            cursor.execute("PRAGMA table_info(bets)")
            print("\n📋 Updated bets table structure:")
            for column in cursor.fetchall():
                print(f"  - {column[1]} ({column[2]})")
            
            conn.close()
            return True
        else:
            print("❌ Failed to add sport_name column")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def update_existing_bets():
    """Update existing bets with sport_name based on match_name"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Updating existing bets with sport_name...")
        
        # Get all pending bets without sport_name
        cursor.execute("""
            SELECT id, match_name, match_id 
            FROM bets 
            WHERE sport_name IS NULL AND status = 'pending'
        """)
        
        pending_bets = cursor.fetchall()
        print(f"📊 Found {len(pending_bets)} pending bets to update")
        
        updated_count = 0
        
        for bet_id, match_name, match_id in pending_bets:
            # Determine sport from match name
            sport_name = determine_sport_from_match_name(match_name)
            
            if sport_name:
                cursor.execute("""
                    UPDATE bets 
                    SET sport_name = ? 
                    WHERE id = ?
                """, (sport_name, bet_id))
                updated_count += 1
                print(f"  ✅ Bet {bet_id}: {match_name} → {sport_name}")
        
        conn.commit()
        print(f"✅ Updated {updated_count} bets with sport_name")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to update existing bets: {e}")
        return False

def determine_sport_from_match_name(match_name):
    """Determine sport from match name (same logic as settlement service)"""
    if not match_name:
        return None
    
    match_name_lower = match_name.lower()
    
    # Baseball teams
    baseball_teams = ['marines', 'hawks', 'dragons', 'tigers', 'eagles', 'buffaloes', 
                     'giants', 'swallows', 'carp', 'baystars', 'lions', 'fighters', 'orix']
    if any(team in match_name_lower for team in baseball_teams):
        return 'baseball'
    
    # Basketball teams  
    basketball_teams = ['lakers', 'warriors', 'celtics', 'bulls', 'heat', 'knicks', 
                       'nets', 'raptors', 'mavericks', 'rockets', 'spurs', 'thunder']
    if any(team in match_name_lower for team in basketball_teams):
        return 'bsktbl'
    
    # Soccer teams
    soccer_teams = ['united', 'city', 'arsenal', 'chelsea', 'liverpool', 'barcelona', 
                   'real madrid', 'bayern', 'psg', 'juventus', 'milan', 'inter']
    if any(team in match_name_lower for team in soccer_teams):
        return 'soccer'
    
    # Football teams
    football_teams = ['patriots', 'cowboys', 'packers', 'steelers', '49ers', 'chiefs', 
                     'bills', 'ravens', 'eagles', 'giants', 'jets']
    if any(team in match_name_lower for team in football_teams):
        return 'football'
    
    # Default to soccer for unknown teams
    return 'soccer'

if __name__ == "__main__":
    print("🚀 Starting sport_name migration...")
    print("=" * 50)
    
    # Run migration
    if run_migration():
        print("\n🔄 Updating existing bets...")
        update_existing_bets()
        print("\n✅ Migration completed successfully!")
        print("\n📝 Benefits:")
        print("  - Settlement service now uses stored sport_name")
        print("  - More reliable than guessing from match names")
        print("  - Faster settlement (no sport detection needed)")
        print("  - Handles new players/teams automatically")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
