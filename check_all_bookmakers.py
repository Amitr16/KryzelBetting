#!/usr/bin/env python3
"""
Check all bookmaker fields in cricket JSON data to find any that are strings
"""

import json

def check_all_bookmakers():
    """Check all bookmaker fields in cricket data"""
    try:
        with open('Sports Pre Match/cricket/cricket_odds.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("🏏 Checking all bookmaker fields in cricket data...")
        
        odds_data = data['odds_data']
        scores = odds_data['scores']
        categories = scores['category']
        
        string_bookmakers = []
        list_bookmakers = []
        
        for cat_idx, category in enumerate(categories):
            if 'matches' not in category:
                continue
                
            matches = category['matches']
            if isinstance(matches, dict) and 'match' in matches:
                match = matches['match']
                if isinstance(match, dict) and 'odds' in match:
                    odds = match['odds']
                    if 'type' in odds:
                        for type_idx, odd_type in enumerate(odds['type']):
                            if 'bookmaker' in odd_type:
                                bookmaker = odd_type['bookmaker']
                                if isinstance(bookmaker, str):
                                    string_bookmakers.append({
                                        'category': category.get('name', 'Unknown'),
                                        'match_id': match.get('id', 'Unknown'),
                                        'type_id': odd_type.get('id', 'Unknown'),
                                        'bookmaker_value': bookmaker[:100] + '...' if len(bookmaker) > 100 else bookmaker
                                    })
                                elif isinstance(bookmaker, list):
                                    list_bookmakers.append({
                                        'category': category.get('name', 'Unknown'),
                                        'match_id': match.get('id', 'Unknown'),
                                        'type_id': odd_type.get('id', 'Unknown'),
                                        'bookmaker_count': len(bookmaker)
                                    })
        
        print(f"\n📊 Summary:")
        print(f"String bookmakers: {len(string_bookmakers)}")
        print(f"List bookmakers: {len(list_bookmakers)}")
        
        if string_bookmakers:
            print(f"\n❌ Found {len(string_bookmakers)} string bookmakers:")
            for item in string_bookmakers[:5]:  # Show first 5
                print(f"   Category: {item['category']}")
                print(f"   Match ID: {item['match_id']}")
                print(f"   Type ID: {item['type_id']}")
                print(f"   Bookmaker: {item['bookmaker_value']}")
                print()
            
            if len(string_bookmakers) > 5:
                print(f"   ... and {len(string_bookmakers) - 5} more")
        
        if list_bookmakers:
            print(f"\n✅ Found {len(list_bookmakers)} list bookmakers:")
            for item in list_bookmakers[:3]:  # Show first 3
                print(f"   Category: {item['category']}")
                print(f"   Match ID: {item['match_id']}")
                print(f"   Type ID: {item['type_id']}")
                print(f"   Bookmaker count: {item['bookmaker_count']}")
                print()
            
            if len(list_bookmakers) > 3:
                print(f"   ... and {len(list_bookmakers) - 3} more")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_all_bookmakers()
