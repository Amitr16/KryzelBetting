#!/usr/bin/env python3
"""
Detailed debug script to examine cricket JSON structure
"""

import json
from pathlib import Path

def examine_cricket_structure():
    """Examine the cricket JSON structure in detail"""
    cricket_file = Path("Sports Pre Match/cricket/cricket_odds.json")
    
    with open(cricket_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("🏏 Detailed Cricket JSON Structure Analysis")
    print("=" * 60)
    
    # Examine metadata
    print("\n📋 METADATA:")
    metadata = data.get('metadata', {})
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    # Examine odds_data
    print("\n🎯 ODDS_DATA:")
    odds_data = data.get('odds_data', {})
    for key, value in odds_data.items():
        print(f"   {key}: {type(value)}")
        if isinstance(value, dict):
            print(f"      Keys: {list(value.keys())}")
        elif isinstance(value, list):
            print(f"      List length: {len(value)}")
            if value:
                print(f"      First item type: {type(value[0])}")
                if isinstance(value[0], dict):
                    print(f"      First item keys: {list(value[0].keys())}")
    
    # Deep dive into scores
    print("\n🏏 SCORES DETAILED ANALYSIS:")
    scores = odds_data.get('scores', {})
    if isinstance(scores, dict):
        print(f"Scores is a dict with {len(scores)} keys")
        print(f"Score keys: {list(scores.keys())}")
        
        # Look at first few score entries
        for i, (key, value) in enumerate(list(scores.items())[:3]):
            print(f"\n   Score entry {i+1} - Key: {key}")
            print(f"      Type: {type(value)}")
            if isinstance(value, dict):
                print(f"      Keys: {list(value.keys())}")
                # Show first few values
                for k, v in list(value.items())[:5]:
                    print(f"         {k}: {v}")
            elif isinstance(value, list):
                print(f"      List length: {len(value)}")
                if value:
                    print(f"      First item: {value[0]}")
    
    # Look for any nested structures that might contain match data
    print("\n🔍 SEARCHING FOR MATCH DATA IN NESTED STRUCTURES:")
    def search_for_matches(obj, path="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Look for cricket-specific keywords
                cricket_keywords = ['match', 'game', 'inning', 'over', 'wicket', 'run', 'batsman', 'bowler']
                if any(keyword in str(key).lower() or keyword in str(value).lower() for keyword in cricket_keywords):
                    print(f"      🏏 Found cricket-related data at {current_path}")
                    if isinstance(value, dict):
                        print(f"         Keys: {list(value.keys())}")
                    elif isinstance(value, list):
                        print(f"         List length: {len(value)}")
                
                search_for_matches(value, current_path, max_depth, current_depth + 1)
        
        elif isinstance(obj, list) and len(obj) > 0:
            current_path = f"{path}[list]"
            if len(obj) > 0:
                print(f"      📋 List found at {current_path}, length: {len(obj)}")
                if isinstance(obj[0], dict):
                    print(f"         First item keys: {list(obj[0].keys())}")
                search_for_matches(obj[0], current_path, max_depth, current_depth + 1)
    
    search_for_matches(data)

if __name__ == "__main__":
    examine_cricket_structure()
