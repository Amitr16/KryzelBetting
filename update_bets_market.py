#!/usr/bin/env python3
"""
Script to update all existing bets to have market = "1"
"""

import sqlite3
import os

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')

def update_bets_market():
    """Update all existing bets to have market = '1'"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get count of existing bets
        cursor.execute("SELECT COUNT(*) FROM bets")
        bet_count = cursor.fetchone()[0]
        
        print(f"Found {bet_count} bets in the database")
        
        if bet_count == 0:
            print("No bets to update!")
            return
        
        # Update all bets to have market = "1"
        cursor.execute("UPDATE bets SET market = '1' WHERE market IS NULL OR market = ''")
        
        # Commit the changes
        conn.commit()
        
        # Get updated count
        cursor.execute("SELECT COUNT(*) FROM bets WHERE market = '1'")
        updated_count = cursor.fetchone()[0]
        
        print(f"✅ Successfully updated {updated_count} bets to have market = '1'")
        
        # Show sample of updated bets
        cursor.execute("SELECT id, match_id, selection, market FROM bets LIMIT 5")
        sample_bets = cursor.fetchall()
        
        print("\nSample updated bets:")
        for bet in sample_bets:
            print(f"  Bet ID: {bet[0]}, Match: {bet[1]}, Selection: {bet[2]}, Market: {bet[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔧 Updating existing bets to have market = '1'...")
    update_bets_market()
    print("✅ Done!")
