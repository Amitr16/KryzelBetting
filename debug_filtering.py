#!/usr/bin/env python3
"""
Debug script to check why disabled events are still showing
"""

import sqlite3
import os
import json
from pathlib import Path

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')
BASE_SPORTS_PATH = Path(__file__).parent / "Sports Pre Match"

def debug_filtering():
    """Debug the filtering logic"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get disabled events
        cursor.execute("SELECT * FROM disabled_events")
        disabled_events = cursor.fetchall()
        
        print("🔍 Disabled events in database:")
        for event in disabled_events:
            print(f"  Event Key: {event[0]}, Sport: {event[1]}, Event Name: {event[2]}, Market: {event[3]}")
        
        # Check if the specific event exists in JSON
        soccer_file = BASE_SPORTS_PATH / "soccer" / "soccer_odds.json"
        if soccer_file.exists():
            with open(soccer_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n🔍 Looking for event 6267403 in soccer JSON...")
            
            # Search for the event
            found_event = None
            if 'odds_data' in data and 'scores' in data['odds_data']:
                scores = data['odds_data']['scores']
                if 'categories' in scores:
                    for category in scores['categories']:
                        if 'matches' in category:
                            for match in category['matches']:
                                if match.get('id') == '6267403':
                                    found_event = match
                                    print(f"✅ Found event 6267403: {match.get('localteam', {}).get('name', 'Unknown')} vs {match.get('awayteam', {}).get('name', 'Unknown')}")
                                    break
                        if found_event:
                            break
            
            if not found_event:
                print("❌ Event 6267403 not found in soccer JSON")
        
        # Test the filtering logic
        print(f"\n🔍 Testing filtering logic...")
        
        # Simulate the filtering logic
        disabled_keys = set(row[1] for row in disabled_events)  # Using sport field as event_key
        print(f"Disabled keys: {disabled_keys}")
        
        # Check if 6267403_market_1 is in disabled keys
        target_key = "6267403_market_1"
        if target_key in disabled_keys:
            print(f"✅ {target_key} is in disabled keys")
        else:
            print(f"❌ {target_key} is NOT in disabled keys")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Debugging filtering logic...")
    debug_filtering()
    print("✅ Done!")
