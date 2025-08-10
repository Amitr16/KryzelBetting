#!/usr/bin/env python3
"""
Debug script to test cricket data extraction for sportsbook UI
This will test the same logic that the frontend uses
"""

import json
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import the json_sports module
sys.path.append('src')

from routes.json_sports import extract_events_from_json, SPORTS_CONFIG

def test_cricket_extraction():
    """Test cricket data extraction using the same logic as the sportsbook UI"""
    print("🏏 Testing Cricket Data Extraction for Sportsbook UI")
    print("=" * 60)
    
    # Load the cricket JSON file
    cricket_file = Path("Sports Pre Match/cricket/cricket_odds.json")
    
    if not cricket_file.exists():
        print(f"❌ Cricket file not found: {cricket_file}")
        return
    
    try:
        with open(cricket_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Successfully loaded cricket file: {cricket_file}")
        print(f"📊 File size: {cricket_file.stat().st_size} bytes")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Get cricket sport config
    cricket_config = SPORTS_CONFIG.get('cricket', {})
    print(f"\n📋 Cricket config: {cricket_config}")
    
    # Test the extraction using the same function the sportsbook UI uses
    print("\n🔍 Testing extract_events_from_json function...")
    events = extract_events_from_json(data, cricket_config, 'cricket')
    
    print(f"\n📊 Extraction Results:")
    print(f"Total events extracted: {len(events)}")
    
    if events:
        print(f"\n✅ Successfully extracted {len(events)} cricket events:")
        for i, event in enumerate(events[:3]):  # Show first 3 events
            print(f"\n🏏 Event {i+1}:")
            print(f"   ID: {event.get('id', 'N/A')}")
            print(f"   Teams: {event.get('home_team', 'N/A')} vs {event.get('away_team', 'N/A')}")
            print(f"   League: {event.get('league', 'N/A')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Status: {event.get('status', 'N/A')}")
            print(f"   Odds: {event.get('odds', 'N/A')}")
        
        if len(events) > 3:
            print(f"\n... and {len(events) - 3} more events")
    else:
        print("\n❌ No cricket events extracted!")
        print("This explains why cricket isn't showing in the sportsbook UI")
        
        # Let's debug why no events were extracted
        print("\n🔍 Debugging extraction failure...")
        
        # Check the data structure
        if 'scores' in data and 'odds_data' in data:
            scores = data['odds_data']['scores']
            print(f"✅ Found odds_data.scores structure")
            print(f"   Scores keys: {list(scores.keys())}")
            
            if 'category' in scores:
                categories = scores['category']
                print(f"✅ Found category structure")
                print(f"   Category type: {type(categories)}")
                if isinstance(categories, list):
                    print(f"   Number of categories: {len(categories)}")
                    
                    # Look at first category
                    if categories:
                        first_category = categories[0]
                        print(f"   First category keys: {list(first_category.keys())}")
                        
                        if 'matches' in first_category:
                            matches = first_category['matches']
                            print(f"   Matches type: {type(matches)}")
                            print(f"   Matches keys: {list(matches.keys()) if isinstance(matches, dict) else 'N/A'}")
                            
                            if isinstance(matches, dict) and 'match' in matches:
                                match = matches['match']
                                print(f"   Match type: {type(match)}")
                                if isinstance(match, dict):
                                    print(f"   Match keys: {list(match.keys())}")
                                    print(f"   Local team: {match.get('localteam', 'N/A')}")
                                    print(f"   Away team: {match.get('awayteam', 'N/A')}")
                                    print(f"   Visitorteam: {match.get('visitorteam', 'N/A')}")
                                    print(f"   Has odds: {'odds' in match}")
                                    if 'odds' in match:
                                        print(f"   Odds structure: {list(match['odds'].keys())}")
                else:
                    print(f"   Category is not a list: {categories}")
            else:
                print(f"❌ No 'category' found in scores")
        else:
            print(f"❌ Expected structure not found")
            print(f"   Top level keys: {list(data.keys())}")
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG SUMMARY")
    print("=" * 60)
    
    if events:
        print("✅ Cricket data is being extracted correctly")
        print("❓ The issue might be elsewhere in the sportsbook UI")
    else:
        print("❌ Cricket data extraction is failing")
        print("💡 This is why cricket isn't showing in the sportsbook UI")

if __name__ == "__main__":
    test_cricket_extraction()
