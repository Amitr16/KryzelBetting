#!/usr/bin/env python3
"""
Check the bookmaker structure in cricket JSON data
"""

import json

def check_bookmaker_structure():
    """Check the structure of the bookmaker field in cricket odds"""
    try:
        with open('Sports Pre Match/cricket/cricket_odds.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("🏏 Checking bookmaker structure in cricket odds...")
        
        # Navigate to the first match's odds
        odds_data = data['odds_data']
        scores = odds_data['scores']
        category = scores['category'][0]  # First category
        matches = category['matches']
        match = matches['match']
        odds = match['odds']
        
        print(f"Odds structure: {list(odds.keys())}")
        
        if 'type' in odds:
            odd_type = odds['type'][0]  # First type
            print(f"First odd_type keys: {list(odd_type.keys())}")
            
            if 'bookmaker' in odd_type:
                bookmaker = odd_type['bookmaker']
                print(f"Bookmaker type: {type(bookmaker)}")
                print(f"Bookmaker value: {bookmaker}")
                
                if isinstance(bookmaker, str):
                    print("✅ Bookmaker is a string - this explains the error!")
                elif isinstance(bookmaker, list):
                    print("✅ Bookmaker is a list")
                    if bookmaker:
                        print(f"First bookmaker: {bookmaker[0]}")
                else:
                    print(f"❓ Bookmaker is {type(bookmaker)}")
            else:
                print("❌ No 'bookmaker' field found in odd_type")
        else:
            print("❌ No 'type' field found in odds")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_bookmaker_structure()
