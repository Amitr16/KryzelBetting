#!/usr/bin/env python3
"""
Debug script to test cricket extraction directly
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from src.routes.json_sports import load_sport_json, extract_events_from_json, SPORTS_CONFIG

def test_cricket_extraction():
    """Test cricket extraction directly"""
    print("=== TESTING CRICKET EXTRACTION ===")
    
    # Test cricket specifically
    sport_name = 'cricket'
    print(f"Testing sport: {sport_name}")
    
    # Load cricket JSON
    json_data = load_sport_json(sport_name)
    if json_data:
        print(f"✅ Cricket JSON loaded successfully")
        print(f"JSON keys: {list(json_data.keys())}")
        
        if 'odds_data' in json_data:
            print(f"✅ Found odds_data")
            odds_data = json_data['odds_data']
            print(f"odds_data keys: {list(odds_data.keys())}")
            
            if 'scores' in odds_data:
                print(f"✅ Found scores")
                scores = odds_data['scores']
                print(f"scores keys: {list(scores.keys())}")
                
                if 'category' in scores:
                    print(f"✅ Found category")
                    categories = scores['category']
                    print(f"Number of categories: {len(categories) if isinstance(categories, list) else 1}")
                    
                    # Look at first category
                    if isinstance(categories, list) and categories:
                        first_category = categories[0]
                        print(f"First category keys: {list(first_category.keys())}")
                        
                        if 'matches' in first_category:
                            print(f"✅ Found matches")
                            matches = first_category['matches']
                            print(f"matches type: {type(matches)}")
                            
                            if isinstance(matches, dict) and 'match' in matches:
                                print(f"✅ Found match")
                                match = matches['match']
                                print(f"Match keys: {list(match.keys())}")
                                
                                if 'odds' in match:
                                    print(f"✅ Found odds")
                                    odds = match['odds']
                                    print(f"Odds keys: {list(odds.keys())}")
                                    
                                    if 'type' in odds:
                                        print(f"✅ Found type array")
                                        type_array = odds['type']
                                        print(f"Type array length: {len(type_array) if isinstance(type_array, list) else 'not list'}")
                                        
                                        if isinstance(type_array, list) and type_array:
                                            first_type = type_array[0]
                                            print(f"First type keys: {list(first_type.keys())}")
                                            
                                            if 'bookmaker' in first_type:
                                                print(f"✅ Found bookmaker")
                                                bookmakers = first_type['bookmaker']
                                                print(f"Bookmakers length: {len(bookmakers) if isinstance(bookmakers, list) else 'not list'}")
                                                
                                                if isinstance(bookmakers, list) and bookmakers:
                                                    first_bookmaker = bookmakers[0]
                                                    print(f"First bookmaker keys: {list(first_bookmaker.keys())}")
                                                    
                                                    if 'odd' in first_bookmaker:
                                                        print(f"✅ Found odd array")
                                                        odds_array = first_bookmaker['odd']
                                                        print(f"Odds array length: {len(odds_array) if isinstance(odds_array, list) else 'not list'}")
                                                        
                                                        if isinstance(odds_array, list) and odds_array:
                                                            first_odd = odds_array[0]
                                                            print(f"First odd keys: {list(first_odd.keys())}")
                                                            print(f"First odd: {first_odd}")
        else:
            print(f"❌ No odds_data found")
    else:
        print(f"❌ Failed to load cricket JSON")
    
    print("\n=== TESTING EXTRACT_EVENTS_FROM_JSON ===")
    
    # Test the actual extraction function
    if json_data:
        events = extract_events_from_json(json_data, SPORTS_CONFIG[sport_name], sport_name)
        print(f"Events extracted: {len(events)}")
        
        if events:
            print(f"First event: {events[0]}")
        else:
            print("No events extracted")
    else:
        print("Cannot test extraction - no JSON data")

if __name__ == "__main__":
    test_cricket_extraction()
