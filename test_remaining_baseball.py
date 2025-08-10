#!/usr/bin/env python3

import requests
import json

def test_remaining_baseball():
    """Test if the remaining baseball matches are in the home endpoint"""
    
    # Test the baseball home endpoint
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/baseball/home?json=1"
    
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for matches 341057 and 341059
            matches_to_find = ['341057', '341059']
            found_matches = []
            
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
                                        if match_id in matches_to_find:
                                            print(f"*** FOUND MATCH {match_id} ***")
                                            print(f"  Home: {match.get('localteam', {}).get('@name', 'Unknown')}")
                                            print(f"  Away: {match.get('awayteam', {}).get('@name', 'Unknown')}")
                                            print(f"  Status: {match.get('@status', 'Unknown')}")
                                            print(f"  Home Score: {match.get('localteam', {}).get('@totalscore', 'Unknown')}")
                                            print(f"  Away Score: {match.get('awayteam', {}).get('@totalscore', 'Unknown')}")
                                            print(f"  Category: {category.get('@name', 'Unknown')}")
                                            found_matches.append(match_id)
                                else:
                                    match_id = match_list.get('@id', 'Unknown')
                                    if match_id in matches_to_find:
                                        print(f"*** FOUND MATCH {match_id} ***")
                                        print(f"  Home: {match_list.get('localteam', {}).get('@name', 'Unknown')}")
                                        print(f"  Away: {match_list.get('awayteam', {}).get('@name', 'Unknown')}")
                                        print(f"  Status: {match_list.get('@status', 'Unknown')}")
                                        print(f"  Home Score: {match_list.get('localteam', {}).get('@totalscore', 'Unknown')}")
                                        print(f"  Away Score: {match_list.get('awayteam', {}).get('@totalscore', 'Unknown')}")
                                        print(f"  Category: {category.get('@name', 'Unknown')}")
                                        found_matches.append(match_id)
            
            missing_matches = [match_id for match_id in matches_to_find if match_id not in found_matches]
            if missing_matches:
                print(f"❌ Missing matches: {missing_matches}")
            else:
                print("✅ All remaining baseball matches found!")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_remaining_baseball()
