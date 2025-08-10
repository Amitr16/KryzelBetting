#!/usr/bin/env python3
"""
Script to add market column to bets table
"""

import sqlite3
import os

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')

def add_market_column():
    """Add market column to bets table"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if market column already exists
        cursor.execute("PRAGMA table_info(bets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'market' in columns:
            print("Market column already exists!")
            return
        
        # Add market column
        cursor.execute("ALTER TABLE bets ADD COLUMN market TEXT")
        
        # Commit the changes
        conn.commit()
        
        print("✅ Successfully added 'market' column to bets table!")
        
        # Show table structure
        cursor.execute("PRAGMA table_info(bets)")
        print("\nUpdated bets table structure:")
        for column in cursor.fetchall():
            print(f"  {column[1]} ({column[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔧 Adding market column to bets table...")
    add_market_column()
    print("✅ Done!")
