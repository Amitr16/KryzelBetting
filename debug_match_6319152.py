#!/usr/bin/env python3
"""
Debug why match 6319152 (Forli vs Ancona) is not being auto-settled
"""

import requests
import json

def check_match_6319152():
    """Check if match 6319152 is completed in soccer data"""
    
    # Check soccer/home endpoint first (most recent completed matches)
    print("🔍 CHECKING SOCCER/HOME ENDPOINT")
    print("=" * 50)
    
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/soccer/home"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Search for match 6319152
            found = False
            if 'scores' in data and 'categories' in data['scores']:
                categories = data['scores']['categories']
                if not isinstance(categories, list):
                    categories = [categories]
                
                for category in categories:
                    if 'matches' in category:
                        matches = category['matches']
                        if not isinstance(matches, list):
                            matches = [matches]
                        
                        for match in matches:
                            if isinstance(match, dict) and match.get('id') == '6319152':
                                found = True
                                print(f"✅ FOUND MATCH 6319152 in soccer/home")
                                print(f"   Status: {match.get('status', 'Unknown')}")
                                print(f"   Home: {match.get('localteam', {}).get('name', 'Unknown')}")
                                print(f"   Away: {match.get('visitorteam', {}).get('name', 'Unknown')}")
                                print(f"   Score: {match.get('localteam', {}).get('totalscore', '?')} - {match.get('visitorteam', {}).get('totalscore', '?')}")
                                break
                        if found:
                            break
                    if found:
                        break
            
            if not found:
                print("❌ Match 6319152 not found in soccer/home")
        else:
            print(f"❌ Failed to fetch soccer/home: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking soccer/home: {e}")
    
    # Check soccer/d-1 endpoint (yesterday's matches)
    print("\n🔍 CHECKING SOCCER/D-1 ENDPOINT")
    print("=" * 50)
    
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/soccer/d-1"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Search for match 6319152
            found = False
            if 'scores' in data and 'categories' in data['scores']:
                categories = data['scores']['categories']
                if not isinstance(categories, list):
                    categories = [categories]
                
                for category in categories:
                    if 'matches' in category:
                        matches = category['matches']
                        if not isinstance(matches, list):
                            matches = [matches]
                        
                        for match in matches:
                            if isinstance(match, dict) and match.get('id') == '6319152':
                                found = True
                                print(f"✅ FOUND MATCH 6319152 in soccer/d-1")
                                print(f"   Status: {match.get('status', 'Unknown')}")
                                print(f"   Home: {match.get('localteam', {}).get('name', 'Unknown')}")
                                print(f"   Away: {match.get('visitorteam', {}).get('name', 'Unknown')}")
                                print(f"   Score: {match.get('localteam', {}).get('totalscore', '?')} - {match.get('visitorteam', {}).get('totalscore', '?')}")
                                break
                        if found:
                            break
                    if found:
                        break
            
            if not found:
                print("❌ Match 6319152 not found in soccer/d-1")
        else:
            print(f"❌ Failed to fetch soccer/d-1: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking soccer/d-1: {e}")
    
    # Check soccer/d-2 endpoint (day before yesterday)
    print("\n🔍 CHECKING SOCCER/D-2 ENDPOINT")
    print("=" * 50)
    
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/soccer/d-2"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Search for match 6319152
            found = False
            if 'scores' in data and 'categories' in data['scores']:
                categories = data['scores']['categories']
                if not isinstance(categories, list):
                    categories = [categories]
                
                for category in categories:
                    if 'matches' in category:
                        matches = category['matches']
                        if not isinstance(matches, list):
                            matches = [matches]
                        
                        for match in matches:
                            if isinstance(match, dict) and match.get('id') == '6319152':
                                found = True
                                print(f"✅ FOUND MATCH 6319152 in soccer/d-2")
                                print(f"   Status: {match.get('status', 'Unknown')}")
                                print(f"   Home: {match.get('localteam', {}).get('name', 'Unknown')}")
                                print(f"   Away: {match.get('visitorteam', {}).get('name', 'Unknown')}")
                                print(f"   Score: {match.get('localteam', {}).get('totalscore', '?')} - {match.get('visitorteam', {}).get('totalscore', '?')}")
                                break
                        if found:
                            break
                    if found:
                        break
            
            if not found:
                print("❌ Match 6319152 not found in soccer/d-2")
        else:
            print(f"❌ Failed to fetch soccer/d-2: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking soccer/d-2: {e}")

if __name__ == "__main__":
    print("🚀 DEBUGGING MATCH 6319152 (Forli vs Ancona)")
    print("=" * 60)
    check_match_6319152()
