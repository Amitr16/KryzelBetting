import requests
import json

def test_disabled_events():
    try:
        # Test the soccer events API
        response = requests.get('http://localhost:5000/api/events/soccer')
        data = response.json()
        
        print(f"Total events returned: {len(data)}")
        print("\nFirst 5 events:")
        for i, event in enumerate(data[:5]):
            print(f"{i+1}. Event ID: {event.get('id')}, Teams: {event.get('home_team')} vs {event.get('away_team')}")
        
        # Check if the disabled event 975970 is present
        disabled_event_found = False
        for event in data:
            if str(event.get('id')) == '975970':
                disabled_event_found = True
                print(f"\n⚠️ DISABLED EVENT FOUND: Event ID 975970 - {event.get('home_team')} vs {event.get('away_team')}")
                break
        
        if not disabled_event_found:
            print("\n✅ Disabled event 975970 is NOT present in the API response (correct behavior)")
        else:
            print("\n❌ Disabled event 975970 is still present in the API response (incorrect behavior)")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    test_disabled_events()
