import requests
import json

def test_sport_markets(sport_name):
    """Test if a sport has secondary markets"""
    try:
        r = requests.get(f'http://localhost:5000/api/sports/events/{sport_name}')
        data = r.json()
        
        print(f"🎯 {sport_name.upper()} Markets:")
        for i, event in enumerate(data[:2]):  # Check first 2 events
            print(f"  Event {i+1}: {event['home_team']} vs {event['away_team']}")
            odds = event.get('odds', {})
            if odds:
                for market, market_odds in odds.items():
                    print(f"    {market}: {market_odds}")
            else:
                print("    No odds available")
        print()
        
    except Exception as e:
        print(f"❌ Error testing {sport_name}: {e}")

# Test sports with secondary markets
sports = ['soccer', 'basketball', 'tennis', 'table_tennis', 'darts', 'volleyball']

for sport in sports:
    test_sport_markets(sport)
