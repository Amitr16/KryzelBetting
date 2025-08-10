import requests
import json

def test_specific_event():
    try:
        # Test the events endpoint
        response = requests.get('http://localhost:5000/api/sports/events/soccer')
        data = response.json()
        
        print(f"Total events returned: {len(data)}")
        
        # Look for event 975970 specifically
        event_975970 = None
        for event in data:
            if str(event.get('id')) == '975970':
                event_975970 = event
                break
        
        if event_975970:
            print(f"\n✅ Found event 975970: {event_975970.get('home_team')} vs {event_975970.get('away_team')}")
            print(f"Available markets: {list(event_975970.get('odds', {}).keys())}")
            
            # Check if market 2 is present
            odds = event_975970.get('odds', {})
            market_2_present = False
            for market_key, market_data in odds.items():
                if market_key == '2' or (isinstance(market_data, list) and len(market_data) > 0):
                    print(f"Market '{market_key}': {market_data}")
                    if market_key == '2':
                        market_2_present = True
            
            if market_2_present:
                print("\n❌ Market 2 is still present (should be filtered out)")
            else:
                print("\n✅ Market 2 is correctly filtered out")
                
        else:
            print("\n❌ Event 975970 not found in the API response")
            
    except Exception as e:
        print(f"Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_event()
