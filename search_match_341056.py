#!/usr/bin/env python3

import requests

def search_match_341056():
    # Test the baseball historical endpoint directly
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/baseball/home?json=1"
    
    try:
        print(f"Searching for match ID: 341056")
        print(f"URL: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Look for matches
            if isinstance(data, dict) and 'scores' in data:
                scores = data['scores']
                if 'category' in scores:
                    categories = scores['category']
                    if isinstance(categories, list):
                        print(f"Found {len(categories)} categories")
                        
                        match_found = False
                        for i, category in enumerate(categories):
                            print(f"  Category {i}: {category.get('@name', 'Unknown')}")
                            
                            # Check if category has direct 'match' array
                            if 'match' in category:
                                match_list = category['match']
                                if isinstance(match_list, list):
                                    print(f"    Found {len(match_list)} matches in category")
                                    for match in match_list:
                                        match_id = match.get('@id', 'Unknown')
                                        if match_id == '341056':
                                            print(f"*** FOUND MATCH 341056 ***")
                                            print(f"  Home: {match.get('localteam', {}).get('@name', 'Unknown')}")
                                            print(f"  Away: {match.get('awayteam', {}).get('@name', 'Unknown')}")
                                            print(f"  Status: {match.get('@status', 'Unknown')}")
                                            print(f"  Category: {category.get('@name', 'Unknown')}")
                                            print(f"  Date: {match.get('@date', 'Unknown')}")
                                            print(f"  Time: {match.get('@time', 'Unknown')}")
                                            match_found = True
                                            break
                                else:
                                    # Single match
                                    match_id = match_list.get('@id', 'Unknown')
                                    if match_id == '341056':
                                        print(f"*** FOUND MATCH 341056 ***")
                                        print(f"  Home: {match_list.get('localteam', {}).get('@name', 'Unknown')}")
                                        print(f"  Away: {match_list.get('awayteam', {}).get('@name', 'Unknown')}")
                                        print(f"  Status: {match_list.get('@status', 'Unknown')}")
                                        print(f"  Category: {category.get('@name', 'Unknown')}")
                                        print(f"  Date: {match_list.get('@date', 'Unknown')}")
                                        print(f"  Time: {match_list.get('@time', 'Unknown')}")
                                        match_found = True
                                        break
                                
                                if match_found:
                                    break
                            
                            # Also check the old nested structure just in case
                            elif 'matches' in category:
                                matches = category['matches']
                                if 'match' in matches:
                                    match_list = matches['match']
                                    if isinstance(match_list, list):
                                        for match in match_list:
                                            match_id = match.get('@id', 'Unknown')
                                            if match_id == '341056':
                                                print(f"*** FOUND MATCH 341056 ***")
                                                print(f"  Home: {match.get('localteam', {}).get('@name', 'Unknown')}")
                                                print(f"  Away: {match.get('awayteam', {}).get('@name', 'Unknown')}")
                                                print(f"  Status: {match.get('@status', 'Unknown')}")
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
                                            print(f"  Category: {category.get('@name', 'Unknown')}")
                                            match_found = True
                                            break
                                    
                                    if match_found:
                                        break
                            
                            if match_found:
                                break
                        
                        if not match_found:
                            print("❌ Match ID 341056 not found in baseball historical data")
                            
                            # Show some sample match IDs to see what's available
                            print("\nSample match IDs found:")
                            count = 0
                            for i, category in enumerate(categories):
                                if count >= 3:  # Only show first 3 categories
                                    break
                                if 'match' in category:
                                    match_list = category['match']
                                    if isinstance(match_list, list):
                                        for match in match_list[:3]:  # Show first 3 matches per category
                                            match_id = match.get('@id', 'Unknown')
                                            home_team = match.get('localteam', {}).get('@name', 'Unknown')
                                            away_team = match.get('awayteam', {}).get('@name', 'Unknown')
                                            print(f"  ID: {match_id} - {home_team} vs {away_team}")
                                    else:
                                        match_id = match_list.get('@id', 'Unknown')
                                        home_team = match_list.get('localteam', {}).get('@name', 'Unknown')
                                        away_team = match_list.get('awayteam', {}).get('@name', 'Unknown')
                                        print(f"  ID: {match_id} - {home_team} vs {away_team}")
                                    count += 1
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    search_match_341056()
