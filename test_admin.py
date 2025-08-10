import requests
import time

def test_connection():
    print("Testing admin app connection...")
    
    # Test if user app is running
    try:
        response = requests.get('http://localhost:5000/api/sports/sports', timeout=5)
        print(f"✅ User app is running: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Found {len(data)} sports")
            for sport in list(data.keys())[:3]:  # Show first 3 sports
                print(f"   - {sport}")
    except Exception as e:
        print(f"❌ User app not running: {e}")
        return False
    
    # Test if admin app is running
    try:
        response = requests.get('http://localhost:8080/api/bets', timeout=5)
        print(f"✅ Admin app is running: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Found {data.get('summary', {}).get('total_bets', 0)} bets")
    except Exception as e:
        print(f"❌ Admin app not running: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()
