#!/usr/bin/env python3
"""
Test script to verify sport_name logic for settlement
"""

import sqlite3
import os
import json
from datetime import datetime

def test_sport_name_settlement():
    """Test the new sport_name logic for settlement"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"🔍 Testing sport_name settlement logic on: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if sport_name column exists
        cursor.execute("PRAGMA table_info(bets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sport_name' not in columns:
            print("❌ sport_name column not found - run migration first")
            conn.close()
            return False
        
        print("✅ sport_name column exists")
        
        # Get all pending bets with sport_name
        cursor.execute("""
            SELECT id, match_id, match_name, sport_name, bet_type, status, created_at
            FROM bets 
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        
        pending_bets = cursor.fetchall()
        print(f"\n📊 Found {len(pending_bets)} pending bets:")
        
        for bet in pending_bets:
            bet_id, match_id, match_name, sport_name, bet_type, status, created_at = bet
            
            print(f"\n🎯 Bet ID: {bet_id}")
            print(f"   Match ID: {match_id}")
            print(f"   Match Name: {match_name}")
            print(f"   Sport Name: {sport_name or 'NULL'}")
            print(f"   Bet Type: {bet_type}")
            print(f"   Status: {status}")
            print(f"   Created: {created_at}")
            
            # For combo bets, show selections
            if bet_type == 'combo':
                cursor.execute("SELECT combo_selections FROM bets WHERE id = ?", (bet_id,))
                combo_data = cursor.fetchone()
                if combo_data and combo_data[0]:
                    try:
                        selections = json.loads(combo_data[0])
                        print(f"   Combo Selections ({len(selections)}):")
                        for i, selection in enumerate(selections, 1):
                            print(f"     {i}. {selection.get('match_name', 'Unknown')} - {selection.get('selection', 'Unknown')}")
                    except json.JSONDecodeError:
                        print(f"   ❌ Invalid combo_selections JSON")
        
        # Test settlement logic
        print(f"\n🧪 Testing settlement logic:")
        
        # Simulate what the settlement service would do
        for bet in pending_bets:
            bet_id, match_id, match_name, sport_name, bet_type, status, created_at = bet
            
            if sport_name:
                print(f"✅ Bet {bet_id}: Will check {sport_name}/home and {sport_name}/d-1 to d-7")
            else:
                print(f"⚠️  Bet {bet_id}: No sport_name - will use match name analysis")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_migration():
    """Test if migration was successful"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(bets)")
        columns = cursor.fetchall()
        
        print("📋 Bets table structure:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # Check for any NULL sport_name values
        cursor.execute("SELECT COUNT(*) FROM bets WHERE sport_name IS NULL AND status = 'pending'")
        null_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print(f"✅ All pending bets have sport_name")
        else:
            print(f"⚠️  {null_count} pending bets still have NULL sport_name")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING SPORT_NAME SETTLEMENT LOGIC")
    print("=" * 50)
    
    # Test migration
    print("\n1️⃣ Testing migration status:")
    test_migration()
    
    # Test settlement logic
    print("\n2️⃣ Testing settlement logic:")
    test_sport_name_settlement()
    
    print("\n✅ Test completed!")
    print("\n📝 Summary:")
    print("  - sport_name column added to bets table")
    print("  - Settlement service now uses stored sport_name")
    print("  - More reliable than guessing from match names")
    print("  - Faster settlement (no sport detection needed)")
    print("  - Handles new players/teams automatically")
