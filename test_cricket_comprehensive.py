#!/usr/bin/env python3
"""
Comprehensive Cricket API Test
"""

import requests
import json
import time
from datetime import datetime

def test_cricket_comprehensive():
    """Test various cricket endpoints to find working ones"""
    
    base_url = "http://www.goalserve.com/getfeed"
    access_token = "e1e6a26b1dfa4f52976f08ddd2a17244"
    
    # Test different cricket endpoints and parameters
    test_urls = [
        # Try without bm=16 (original cricket format)
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10&json=1",
        
        # Try with bm=16 (standard format)
f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10&json=1&bm=16",
        
        # Try different category codes
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket&json=1",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_1&json=1",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_5&json=1",
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_15&json=1",
        
        # Try with date parameters
        f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10&json=1&bm=16&date_start=01.08.2025&date_end=31.08.2025",
f"{base_url}/{access_token}/getodds/soccer?cat=cricket_10&json=1&bm=16&date_start=01.07.2025&date_end=31.07.2025",
        
        # Try different sport endpoints
        f"{base_url}/{access_token}/getodds/cricket?cat=cricket_10&json=1",
        f"{base_url}/{access_token}/getodds/cricket?json=1",
        
        # Try without category
        f"{base_url}/{access_token}/getodds/soccer?json=1&bm=16",
    ]
    
    headers = {
        'User-Agent': 'GoalServe-CricketComprehensive/1.0',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    print("🔍 Comprehensive Cricket API Test")
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
                    # Handle UTF-8 BOM if present
                    text = response.text
                    if text.startswith('\ufeff'):
                        text = text[1:]  # Remove BOM
                    data = json.loads(text)
                    
                    print(f"   ✅ JSON parsed successfully")
                    
                    # Analyze the structure
                    if 'scores' in data:
                        print(f"   📋 Has 'scores' key")
                        scores = data['scores']
                        
                        if 'categories' in scores:
                            categories = scores['categories']
                            if isinstance(categories, list):
                                print(f"   📊 Found {len(categories)} categories")
                                if len(categories) > 0:
                                    print(f"   🎯 Categories: {[cat.get('name', 'Unknown') for cat in categories[:3]]}")
                            else:
                                print(f"   📊 Single category found")
                        elif 'category' in scores:
                            categories = scores['category']
                            if isinstance(categories, list):
                                print(f"   📊 Found {len(categories)} categories (cricket format)")
                                if len(categories) > 0:
                                    print(f"   🎯 Categories: {[cat.get('name', 'Unknown') for cat in categories[:3]]}")
                            else:
                                print(f"   📊 Single category found (cricket format)")
                        else:
                            print(f"   ⚠️ No categories found")
                            
                        # Check for matches
                        if 'categories' in scores and scores['categories']:
                            for cat in scores['categories']:
                                if 'matches' in cat:
                                    matches = cat['matches']
                                    if isinstance(matches, list):
                                        print(f"   🏏 Found {len(matches)} matches in category '{cat.get('name', 'Unknown')}'")
                                    else:
                                        print(f"   🏏 Found 1 match in category '{cat.get('name', 'Unknown')}'")
                        elif 'category' in scores and scores['category']:
                            for cat in scores['category']:
                                if 'matches' in cat:
                                    matches = cat['matches']
                                    if isinstance(matches, dict) and 'match' in matches:
                                        print(f"   🏏 Found 1 match in category '{cat.get('name', 'Unknown')}' (cricket format)")
                                    else:
                                        print(f"   🏏 Found matches in category '{cat.get('name', 'Unknown')}' (cricket format)")
                    else:
                        print(f"   ⚠️ No 'scores' key found")
                    
                    # Save successful response
                    filename = f"cricket_comprehensive_{i}.json"
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
    
    print("✅ Comprehensive cricket API test completed!")

if __name__ == "__main__":
    test_cricket_comprehensive()
