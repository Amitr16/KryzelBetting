#!/usr/bin/env python3
"""
Cricket API Exploration Script
"""

import requests
import json
import time
from datetime import datetime

def test_cricket_api():
    """Test different cricket API endpoints to understand the structure"""
    
    base_url = "http://www.goalserve.com/getfeed"
    access_token = "e1e6a26b1dfa4f52976f08ddd2a17244"
    
    # Test different cricket endpoints
    test_urls = [
        # Current URL (getting 500 error)
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10&json=1",
        
        # Alternative cricket endpoints to try
        f"{base_url}/{access_token}/getodds/cricket?cat=cricket_10&json=1",
        f"{base_url}/{access_token}/getodds/cricket?json=1",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket&json=1",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10&json=1&bm=16",
        
        # Try with date parameters (like other sports)
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10&json=1&bm=16&date_start=06.08.2025&date_end=08.08.2025",
        
        # Try different category codes
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket&json=1",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_1&json=1",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_5&json=1",
    ]
    
    headers = {
        'User-Agent': 'GoalServe-CricketExplorer/1.0',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    print("🔍 Cricket API Exploration")
    print("=" * 50)
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for i, url in enumerate(test_urls, 1):
        print(f"🧪 Test {i}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"   📊 Status: {response.status_code}")
            print(f"   📏 Content-Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON parsed successfully")
                    
                    # Analyze the structure
                    if 'scores' in data:
                        print(f"   📋 Has 'scores' key")
                        if 'category' in data['scores']:
                            print(f"   📋 Has 'scores.category' (Cricket format)")
                            categories = data['scores']['category']
                            if isinstance(categories, list):
                                print(f"   📊 Found {len(categories)} categories")
                            else:
                                print(f"   📊 Single category found")
                        elif 'categories' in data['scores']:
                            print(f"   📋 Has 'scores.categories' (Standard format)")
                    elif 'odds_data' in data:
                        print(f"   📋 Has 'odds_data' key (Standard format)")
                    else:
                        print(f"   ⚠️ Unknown structure")
                    
                    # Save successful response
                    filename = f"cricket_test_{i}_success.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"   💾 Saved to {filename}")
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                    print(f"   📄 Response preview: {response.text[:200]}...")
                    
            elif response.status_code == 500:
                print(f"   ❌ Server Error (500)")
                print(f"   📄 Error response: {response.text[:500]}...")
                
            elif response.status_code == 404:
                print(f"   ❌ Not Found (404)")
                
            elif response.status_code == 429:
                print(f"   ⚠️ Rate Limited (429)")
                
            else:
                print(f"   ❌ HTTP {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            
        print()
        
        # Small delay between requests
        time.sleep(2)
    
    print("✅ Cricket API exploration completed!")

if __name__ == "__main__":
    test_cricket_api()
