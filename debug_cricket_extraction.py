#!/usr/bin/env python3
"""
Debug script to test cricket data extraction from JSON files
This script will help diagnose why cricket data isn't showing up in the admin interface
"""

import json
import os
import sys
from pathlib import Path

def load_cricket_json():
    """Load and parse the cricket odds JSON file"""
    cricket_file = Path("Sports Pre Match/cricket/cricket_odds.json")
    
    if not cricket_file.exists():
        print(f"❌ Cricket file not found: {cricket_file}")
        return None
    
    try:
        with open(cricket_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Successfully loaded cricket file: {cricket_file}")
        print(f"📊 File size: {cricket_file.stat().st_size} bytes")
        return data
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def analyze_cricket_data(data):
    """Analyze the structure and content of cricket data"""
    if not data:
        print("❌ No data to analyze")
        return
    
    print("\n🔍 Analyzing cricket data structure:")
    print(f"Data type: {type(data)}")
    
    if isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")
        
        # Look for common data structures
        for key, value in data.items():
            print(f"\n📁 Key: {key}")
            print(f"   Type: {type(value)}")
            
            if isinstance(value, list):
                print(f"   List length: {len(value)}")
                if value:
                    print(f"   First item type: {type(value[0])}")
                    if isinstance(value[0], dict):
                        print(f"   First item keys: {list(value[0].keys())}")
            elif isinstance(value, dict):
                print(f"   Dict keys: {list(value.keys())}")
            else:
                print(f"   Value: {value}")
    
    elif isinstance(data, list):
        print(f"Data is a list with {len(data)} items")
        if data:
            print(f"First item type: {type(data[0])}")
            if isinstance(data[0], dict):
                print(f"First item keys: {list(data[0].keys())}")

def extract_cricket_matches(data):
    """Extract cricket match information"""
    if not data:
        return []
    
    matches = []
    
    # Try different possible data structures
    if isinstance(data, dict):
        # Look for common keys that might contain match data
        possible_keys = ['matches', 'events', 'games', 'data', 'results', 'fixtures']
        
        for key in possible_keys:
            if key in data and isinstance(data[key], list):
                print(f"\n🎯 Found potential match data in key: {key}")
                matches.extend(extract_from_list(data[key]))
                break
        
        # If no standard keys found, try to find any list that might contain matches
        if not matches:
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"\n🔍 Checking list in key: {key}")
                    potential_matches = extract_from_list(value)
                    if potential_matches:
                        matches.extend(potential_matches)
                        print(f"✅ Found {len(potential_matches)} matches in {key}")
    
    elif isinstance(data, list):
        print("\n🎯 Data is directly a list, extracting matches...")
        matches.extend(extract_from_list(data))
    
    return matches

def extract_from_list(data_list):
    """Extract match information from a list of data"""
    matches = []
    
    for i, item in enumerate(data_list):
        if isinstance(item, dict):
            # Look for common match identifiers
            match_info = {}
            
            # Common cricket match fields
            possible_fields = {
                'id': ['id', 'match_id', 'event_id', 'game_id'],
                'name': ['name', 'title', 'match_name', 'event_name', 'description'],
                'teams': ['teams', 'participants', 'home_team', 'away_team'],
                'date': ['date', 'start_time', 'scheduled_time', 'datetime'],
                'status': ['status', 'state', 'match_status'],
                'odds': ['odds', 'betting_odds', 'markets']
            }
            
            for field_type, field_names in possible_fields.items():
                for field_name in field_names:
                    if field_name in item:
                        match_info[field_type] = item[field_name]
                        break
            
            if match_info:
                matches.append({
                    'index': i,
                    'data': match_info,
                    'raw': item
                })
    
    return matches

def main():
    """Main function to run the cricket extraction debug"""
    print("🏏 Cricket Data Extraction Debug Script")
    print("=" * 50)
    
    # Load the cricket JSON file
    cricket_data = load_cricket_json()
    
    if not cricket_data:
        print("\n❌ Failed to load cricket data. Exiting.")
        return
    
    # Analyze the data structure
    analyze_cricket_data(cricket_data)
    
    # Extract cricket matches
    print("\n" + "=" * 50)
    print("🎯 EXTRACTING CRICKET MATCHES")
    print("=" * 50)
    
    matches = extract_cricket_matches(cricket_data)
    
    if matches:
        print(f"\n✅ Successfully extracted {len(matches)} potential cricket matches:")
        for i, match in enumerate(matches[:5]):  # Show first 5 matches
            print(f"\n🏏 Match {i+1}:")
            for key, value in match['data'].items():
                print(f"   {key}: {value}")
        
        if len(matches) > 5:
            print(f"\n... and {len(matches) - 5} more matches")
    else:
        print("\n❌ No cricket matches found in the data")
        print("This might explain why cricket isn't showing up in the admin interface")
    
    print("\n" + "=" * 50)
    print("🔍 DEBUG SUMMARY")
    print("=" * 50)
    
    if matches:
        print("✅ Cricket data is present and extractable")
        print("❓ The issue might be in the admin interface code")
        print("💡 Check the admin route that processes cricket data")
    else:
        print("❌ No cricket matches found in the JSON data")
        print("💡 The issue is with the data source, not the admin interface")

if __name__ == "__main__":
    main()
