import json
import os
from pathlib import Path

def analyze_sport_markets(sport_name):
    """Analyze markets available for a specific sport"""
    json_file = Path(f"Sports Pre Match/{sport_name}/{sport_name}_odds.json")
    
    if not json_file.exists():
        print(f"❌ No JSON file found for {sport_name}")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get first match with odds
        categories = data['odds_data']['scores']['categories']
        if not categories:
            print(f"❌ No categories found for {sport_name}")
            return
            
        matches = categories[0]['matches']
        if not matches:
            print(f"❌ No matches found for {sport_name}")
            return
            
        match = matches[0]
        if 'odds' not in match:
            print(f"❌ No odds found for {sport_name}")
            return
            
        print(f"🎯 {sport_name.upper()} Markets:")
        for i, odd in enumerate(match['odds'], 1):
            market_name = odd.get('value', 'Unknown')
            print(f"  {i}. {market_name}")
            
            # Show the structure of this market
            if 'bookmakers' in odd and odd['bookmakers']:
                bookmaker = odd['bookmakers'][0]
                if 'odds' in bookmaker:
                    print(f"     Odds structure: {[o.get('value', 'N/A') for o in bookmaker['odds']]}")
        print()
        
    except Exception as e:
        print(f"❌ Error analyzing {sport_name}: {e}")

# Analyze all sports
sports = [
    'soccer', 'basketball', 'tennis', 'hockey', 'handball', 'volleyball', 
    'football', 'baseball', 'cricket', 'rugby', 'rugbyleague', 'table_tennis',
    'boxing', 'mma', 'darts', 'esports', 'futsal'
]

print("🔍 ANALYZING ALL SPORTS MARKETS")
print("=" * 50)
print()

for sport in sports:
    analyze_sport_markets(sport)

print("✅ Analysis complete!")
