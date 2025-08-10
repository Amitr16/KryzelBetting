#!/usr/bin/env python3
"""
Script to clear all bets from the database
"""

import sqlite3
import os

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')

def clear_bets():
    """Delete all rows from the bets table"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM bets")
        count_before = cursor.fetchone()[0]
        
        print(f"Found {count_before} bets in the database")
        
        if count_before == 0:
            print("No bets to delete!")
            return
        
        # Delete all bets
        cursor.execute("DELETE FROM bets")
        
        # Commit the changes
        conn.commit()
        
        # Get count after deletion
        cursor.execute("SELECT COUNT(*) FROM bets")
        count_after = cursor.fetchone()[0]
        
        print(f"Successfully deleted {count_before - count_after} bets!")
        print(f"Remaining bets: {count_after}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🗑️  Clearing all bets from database...")
    clear_bets()
    print("✅ Done!")
