#!/usr/bin/env python3
"""
Script to debug what the GoalServe API is actually returning
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.goalserve_client import OptimizedGoalServeClient
import json

def debug_goalserve_api():
    """Debug what the GoalServe API is returning"""
    print("🔍 Debugging GoalServe API")
    print("=" * 50)
    
    client = OptimizedGoalServeClient()
    
    # Test endpoints
    endpoints = ['soccer/home', 'soccer/d-1', 'soccer/d-2', 'soccer/d-3']
    
    for endpoint in endpoints:
        print(f"\n📊 Testing endpoint: {endpoint}")
        print("-" * 30)
        
        try:
            # Make the API call
            data = client._make_request(endpoint, use_cache=False)
            
            if data:
                print(f"✅ Got data from {endpoint}")
                print(f"Data type: {type(data)}")
                print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Try to extract matches
                matches = client._extract_matches_from_goalserve_data(data)
                print(f"Extracted {len(matches)} matches")
                
                if matches:
                    print("First few matches:")
                    for i, match in enumerate(matches[:3]):
                        print(f"  Match {i+1}: ID={match.get('@id')}, Status={match.get('@status')}")
                        home_team = match.get('localteam', {}).get('@name', 'Unknown')
                        away_team = match.get('visitorteam', {}).get('@name', 'Unknown')
                        print(f"    Teams: {home_team} vs {away_team}")
                else:
                    print("❌ No matches extracted")
                    
                    # Show a sample of the raw data
                    if isinstance(data, dict):
                        print("Sample of raw data structure:")
                        for key, value in list(data.items())[:5]:
                            print(f"  {key}: {type(value)}")
                            if isinstance(value, dict):
                                print(f"    Keys: {list(value.keys())[:5]}")
            else:
                print(f"❌ No data returned from {endpoint}")
                
        except Exception as e:
            print(f"❌ Error with {endpoint}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_goalserve_api()
