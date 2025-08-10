#!/usr/bin/env python3
"""
Script to check disabled_events table
"""

import sqlite3
import os

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')

def check_disabled_events():
    """Check the disabled_events table"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if disabled_events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='disabled_events'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ disabled_events table does not exist!")
            return
        
        print("✅ disabled_events table exists")
        
        # Get all disabled events
        cursor.execute("SELECT * FROM disabled_events")
        disabled_events = cursor.fetchall()
        
        print(f"\nFound {len(disabled_events)} disabled events:")
        for event in disabled_events:
            print(f"  Event Key: {event[0]}, Sport: {event[1]}, Event Name: {event[2]}, Market: {event[3]}")
        
        # Check if the specific event is disabled
        cursor.execute("SELECT * FROM disabled_events WHERE event_key LIKE '%6267403%'")
        specific_event = cursor.fetchall()
        
        if specific_event:
            print(f"\n✅ Event 6267403 is disabled:")
            for event in specific_event:
                print(f"  Event Key: {event[0]}, Sport: {event[1]}, Event Name: {event[2]}, Market: {event[3]}")
        else:
            print(f"\n❌ Event 6267403 is NOT disabled")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Checking disabled_events table...")
    check_disabled_events()
    print("✅ Done!")
