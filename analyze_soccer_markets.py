import json
import os

def analyze_soccer_markets():
    json_file = "Sports Pre Match/soccer/soccer_odds.json"
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    print("🔍 Analyzing soccer markets...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Track markets and their odds count
        market_stats = {}
        total_events = 0
        
        # Navigate the correct structure
        if 'odds_data' in data and 'scores' in data['odds_data']:
            scores = data['odds_data']['scores']
            categories = scores.get('categories', [])
            
            print(f"Found {len(categories)} categories")
            
            # Process each category
            for category in categories:
                matches = category.get('matches', [])
                print(f"Category '{category.get('name', 'Unknown')}': {len(matches)} matches")
                
                # Process each match
                for match in matches:
                    total_events += 1
                    
                    # Check if match has odds
                    if 'odds' in match and match['odds']:
                        odds = match['odds']
                        
                        # Handle odds as list or dict
                        if isinstance(odds, list):
                            # Process each odds item in the list
                            for i, odds_item in enumerate(odds):
                                if isinstance(odds_item, dict):
                                    # Look for bookmakers array
                                    if 'bookmakers' in odds_item:
                                        bookmakers = odds_item['bookmakers']
                                        if isinstance(bookmakers, list):
                                            for bookmaker in bookmakers:
                                                if isinstance(bookmaker, dict) and 'odds' in bookmaker:
                                                    odds_list = bookmaker['odds']
                                                    if isinstance(odds_list, list):
                                                        for odd in odds_list:
                                                            if isinstance(odd, dict) and 'name' in odd:
                                                                market_name = odd['name']
                                                                if market_name not in market_stats:
                                                                    market_stats[market_name] = {
                                                                        'events_with_odds': 0,
                                                                        'total_odds': 0,
                                                                        'sample_odds': []
                                                                    }
                                                                
                                                                market_stats[market_name]['events_with_odds'] += 1
                                                                market_stats[market_name]['total_odds'] += 1
                                                                
                                                                # Store sample odds
                                                                if len(market_stats[market_name]['sample_odds']) < 3:
                                                                    market_stats[market_name]['sample_odds'].append(odd)
                        elif isinstance(odds, dict):
                            # Handle dict structure if needed
                            pass
        
        print(f"\n📊 Analysis Results:")
        print(f"Total events: {total_events}")
        print(f"Markets found: {len(market_stats)}")
        
        print(f"\n🎯 Markets with odds:")
        print("-" * 80)
        
        # Sort by number of events with odds
        sorted_markets = sorted(market_stats.items(), 
                              key=lambda x: x[1]['events_with_odds'], 
                              reverse=True)
        
        for market_name, stats in sorted_markets:
            if stats['events_with_odds'] > 0:
                print(f"✅ {market_name}")
                print(f"   Events with odds: {stats['events_with_odds']}/{total_events}")
                print(f"   Total odds: {stats['total_odds']}")
                print(f"   Sample odds: {stats['sample_odds'][:2]}")
                print()
        
        print(f"\n❌ Markets with NO odds:")
        print("-" * 80)
        for market_name, stats in sorted_markets:
            if stats['events_with_odds'] == 0:
                print(f"❌ {market_name}")
        
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_soccer_markets()
