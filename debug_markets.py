import json
from pathlib import Path

def debug_soccer_markets():
    """Debug soccer markets extraction"""
    json_file = Path("Sports Pre Match/soccer/soccer_odds.json")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    match = data['odds_data']['scores']['categories'][0]['matches'][0]
    
    print("🔍 SOCCER MARKETS DEBUG:")
    for i, odd in enumerate(match['odds']):
        market_name = odd.get('value', 'Unknown')
        print(f"  {i+1}. {market_name}")
        
        if 'bookmakers' in odd and odd['bookmakers']:
            bookmaker = odd['bookmakers'][0]
            if 'odds' in bookmaker:
                odds_values = [o.get('value', 'N/A') for o in bookmaker['odds']]
                print(f"     Odds: {odds_values}")
                
                # Check if this should be match_result
                if market_name.lower() == 'match winner':
                    print(f"     ✅ This should be mapped to 'match_result'")
                    print(f"     Expected: 1={odds_values[0]}, X={odds_values[1]}, 2={odds_values[2]}")
        print()

if __name__ == "__main__":
    debug_soccer_markets()
