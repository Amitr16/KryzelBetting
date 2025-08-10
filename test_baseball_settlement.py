#!/usr/bin/env python3

import requests
import json

def test_baseball_settlement():
    """Test the settlement logic for baseball match 341056"""
    
    # Test the baseball home endpoint
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/baseball/home?json=1"
    
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for match 341056
            match_found = False
            if isinstance(data, dict) and 'scores' in data:
                scores = data['scores']
                if 'category' in scores:
                    categories = scores['category']
                    if isinstance(categories, list):
                        for category in categories:
                            if 'match' in category:
                                match_list = category['match']
                                if isinstance(match_list, list):
                                    for match in match_list:
                                        match_id = match.get('@id', 'Unknown')
                                        if match_id == '341056':
                                            print(f"*** FOUND MATCH 341056 ***")
                                            print(f"  Home: {match.get('localteam', {}).get('@name', 'Unknown')}")
                                            print(f"  Away: {match.get('awayteam', {}).get('@name', 'Unknown')}")
                                            print(f"  Status: {match.get('@status', 'Unknown')}")
                                            print(f"  Home Score: {match.get('localteam', {}).get('@totalscore', 'Unknown')}")
                                            print(f"  Away Score: {match.get('awayteam', {}).get('@totalscore', 'Unknown')}")
                                            print(f"  Category: {category.get('@name', 'Unknown')}")
                                            match_found = True
                                            break
                                else:
                                    match_id = match_list.get('@id', 'Unknown')
                                    if match_id == '341056':
                                        print(f"*** FOUND MATCH 341056 ***")
                                        print(f"  Home: {match_list.get('localteam', {}).get('@name', 'Unknown')}")
                                        print(f"  Away: {match_list.get('awayteam', {}).get('@name', 'Unknown')}")
                                        print(f"  Status: {match_list.get('@status', 'Unknown')}")
                                        print(f"  Home Score: {match_list.get('localteam', {}).get('@totalscore', 'Unknown')}")
                                        print(f"  Away Score: {match_list.get('awayteam', {}).get('@totalscore', 'Unknown')}")
                                        print(f"  Category: {category.get('@name', 'Unknown')}")
                                        match_found = True
                                        break
                                
                                if match_found:
                                    break
                            
                            if match_found:
                                break
            
            if not match_found:
                print("❌ Match 341056 not found in baseball home data")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_baseball_settlement()
