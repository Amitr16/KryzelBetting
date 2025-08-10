#!/usr/bin/env python3

import requests

def find_baseball_matches():
    # Test the baseball historical endpoint directly
    url = "http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/baseball/d-1?json=1"
    
    try:
        print(f"Testing URL: {url}")
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
                        
                        # Look for specific teams from our bets
                        target_teams = ['marines', 'hawks', 'dragons', 'tigers', 'eagles', 'buffaloes']
                        
                        for i, category in enumerate(categories):
                            if 'matches' in category:
                                matches = category['matches']
                                if 'match' in matches:
                                    match_list = matches['match']
                                    if isinstance(match_list, list):
                                        for match in match_list:
                                            home_team = match.get('localteam', {}).get('name', '').lower()
                                            away_team = match.get('visitorteam', {}).get('name', '').lower()
                                            match_id = match.get('@id', 'Unknown')
                                            status = match.get('status', 'Unknown')
                                            
                                            # Check if this match contains any of our target teams
                                            if any(team in home_team or team in away_team for team in target_teams):
                                                print(f"*** FOUND RELEVANT MATCH ***")
                                                print(f"  Home: {match.get('localteam', {}).get('name', 'Unknown')}")
                                                print(f"  Away: {match.get('visitorteam', {}).get('name', 'Unknown')}")
                                                print(f"  ID: {match_id}")
                                                print(f"  Status: {status}")
                                                print(f"  Category: {category.get('name', 'Unknown')}")
                                                print()
                                    else:
                                        home_team = match_list.get('localteam', {}).get('name', '').lower()
                                        away_team = match_list.get('visitorteam', {}).get('name', '').lower()
                                        match_id = match_list.get('@id', 'Unknown')
                                        status = match_list.get('status', 'Unknown')
                                        
                                        if any(team in home_team or team in away_team for team in target_teams):
                                            print(f"*** FOUND RELEVANT MATCH ***")
                                            print(f"  Home: {match_list.get('localteam', {}).get('name', 'Unknown')}")
                                            print(f"  Away: {match_list.get('visitorteam', {}).get('name', 'Unknown')}")
                                            print(f"  ID: {match_id}")
                                            print(f"  Status: {status}")
                                            print(f"  Category: {category.get('name', 'Unknown')}")
                                            print()
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    find_baseball_matches()
