#!/usr/bin/env python3

import requests

def test_baseball_historical():
    # Test the baseball historical endpoint directly
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/baseball/d-1?json=1"
    
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Look for matches
            if isinstance(data, dict) and 'scores' in data:
                scores = data['scores']
                if 'category' in scores:
                    categories = scores['category']
                    if isinstance(categories, list):
                        print(f"Found {len(categories)} categories")
                        for i, category in enumerate(categories):
                            print(f"  Category {i}: {category.get('name', 'Unknown')}")
                            if 'matches' in category:
                                matches = category['matches']
                                if 'match' in matches:
                                    match_list = matches['match']
                                    if isinstance(match_list, list):
                                        print(f"    Found {len(match_list)} matches")
                                        for j, match in enumerate(match_list):
                                            home_team = match.get('localteam', {}).get('name', 'Unknown')
                                            away_team = match.get('visitorteam', {}).get('name', 'Unknown')
                                            match_id = match.get('@id', 'Unknown')
                                            status = match.get('status', 'Unknown')
                                            
                                            print(f"      Match {j}: {home_team} vs {away_team} - ID: {match_id} - Status: {status}")
                                            
                                            # Look for specific teams from our bets
                                            if any(team in home_team.lower() or team in away_team.lower() for team in ['marines', 'hawks', 'dragons', 'tigers', 'eagles', 'buffaloes']):
                                                print(f"        *** FOUND RELEVANT MATCH: {home_team} vs {away_team} ***")
                                    else:
                                        home_team = match_list.get('localteam', {}).get('name', 'Unknown')
                                        away_team = match_list.get('visitorteam', {}).get('name', 'Unknown')
                                        match_id = match_list.get('@id', 'Unknown')
                                        status = match_list.get('status', 'Unknown')
                                        print(f"    Single match: {home_team} vs {away_team} - ID: {match_id} - Status: {status}")
                    else:
                        print(f"Single category: {categories.get('name', 'Unknown')}")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_baseball_historical()
