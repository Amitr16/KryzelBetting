import requests
import json

def test_api():
    try:
        # Test basic connectivity
        print("Testing API connectivity...")
        response = requests.get('http://localhost:5000/api/health')
        print(f"Health check response: {response.status_code}")
        print(f"Response text: {response.text[:200]}")
        
        # Test sports endpoint (correct URL based on blueprint registration)
        print("\nTesting sports endpoint...")
        response = requests.get('http://localhost:5000/api/sports/sports')
        print(f"Sports response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Sports data: {data}")
        
        # Test events endpoint (correct URL based on blueprint registration)
        print("\nTesting events endpoint...")
        response = requests.get('http://localhost:5000/api/sports/events/soccer')
        print(f"Events response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        
        if response.status_code == 200 and response.text.strip():
            try:
                data = response.json()
                print(f"Successfully parsed JSON with {len(data)} events")
                if data:
                    print(f"First event: {data[0]}")
                    
                    # Check if disabled event 975970 is present
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
                        
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
        else:
            print("No valid response from events endpoint")
            
    except Exception as e:
        print(f"Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
