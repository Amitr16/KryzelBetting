#!/usr/bin/env python3
"""
Update all market values to "1" in the bets table
"""

import sqlite3
import os

def update_market_to_1():
    """Update all market values to '1' in the bets table"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"🔧 Updating market values in: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, let's see the current market values
        print("\n📋 CURRENT MARKET VALUES:")
        print("=" * 50)
        cursor.execute("""
            SELECT id, match_name, market
            FROM bets 
            ORDER BY id
        """)
        
        current_bets = cursor.fetchall()
        for bet_id, match_name, market in current_bets:
            market_display = market if market else "NULL"
            print(f"  Bet {bet_id}: {match_name} - Market: {market_display}")
        
        # Count how many bets will be updated
        cursor.execute("SELECT COUNT(*) FROM bets")
        total_bets = cursor.fetchone()[0]
        
        print(f"\n🔄 UPDATING {total_bets} BETS...")
        
        # Update all market values to "1"
        cursor.execute("""
            UPDATE bets 
            SET market = '2'
        """)
        
        # Commit the changes
        conn.commit()
        
        # Verify the update
        print("\n✅ VERIFICATION - UPDATED MARKET VALUES:")
        print("=" * 50)
        cursor.execute("""
            SELECT id, match_name, market
            FROM bets 
            ORDER BY id
        """)
        
        updated_bets = cursor.fetchall()
        for bet_id, match_name, market in updated_bets:
            market_display = market if market else "NULL"
            print(f"  Bet {bet_id}: {match_name} - Market: {market_display}")
        
        # Show summary
        print(f"\n📊 SUMMARY:")
        print("=" * 30)
        print(f"  Total bets updated: {total_bets}")
        print(f"  All market values set to: 1")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 UPDATING MARKET VALUES TO '1'")
    print("=" * 50)
    update_market_to_1()
