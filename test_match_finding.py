#!/usr/bin/env python3
"""
Script to test if the settlement service can find the specific completed match
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.bet_settlement_service import BetSettlementService
from src.main import app

def test_match_finding():
    """Test if we can find the specific completed match"""
    print("🔍 Testing Match Finding for Settlement")
    print("=" * 50)
    
    # Create settlement service with Flask app
    service = BetSettlementService(app)
    
    # The match we're looking for
    target_match_id = "6220376"
    target_match_name = "Adelaide Croatia Raiders vs Campbelltown City"
    
    print(f"🎯 Looking for match: {target_match_name} (ID: {target_match_id})")
    
    # Test the GoalServe client directly
    client = service.client
    
    # Check soccer home endpoint
    print("\n📊 Checking soccernew/home endpoint...")
    try:
        home_data = client._make_request('soccernew/home', use_cache=False)
        if home_data:
            matches = client._extract_matches_from_goalserve_data(home_data)
            print(f"Found {len(matches)} matches in soccernew/home")
            
            # Look for our target match
            for match in matches:
                match_id = match.get('@id')
                if match_id == target_match_id:
                    print(f"✅ FOUND TARGET MATCH in soccernew/home!")
                    print(f"  ID: {match_id}")
                    print(f"  Status: {match.get('@status')}")
                    print(f"  Home Team: {match.get('localteam', {}).get('@name')}")
                    print(f"  Away Team: {match.get('visitorteam', {}).get('@name')}")
                    print(f"  Home Score: {match.get('localteam', {}).get('@goals')}")
                    print(f"  Away Score: {match.get('visitorteam', {}).get('@goals')}")
                    
                    # Parse for settlement
                    event = service._parse_match_for_settlement(match, 'soccer', 'soccernew/home')
                    if event:
                        print(f"  Parsed Event: {event}")
                        print(f"  Is Completed: {event.get('is_completed')}")
                        print(f"  Is Cancelled: {event.get('is_cancelled')}")
                    return True
        else:
            print("❌ No data from soccernew/home")
    except Exception as e:
        print(f"❌ Error checking soccernew/home: {e}")
    
    # Check historical data
    print("\n📊 Checking historical data...")
    for days_ago in range(1, 4):
        try:
            endpoint = f'soccernew/d-{days_ago}'
            print(f"Checking {endpoint}...")
            historical_data = client._make_request(endpoint, use_cache=False)
            if historical_data:
                matches = client._extract_matches_from_goalserve_data(historical_data)
                print(f"Found {len(matches)} matches in {endpoint}")
                
                # Look for our target match
                for match in matches:
                    match_id = match.get('@id')
                    if match_id == target_match_id:
                        print(f"✅ FOUND TARGET MATCH in {endpoint}!")
                        print(f"  ID: {match_id}")
                        print(f"  Status: {match.get('@status')}")
                        print(f"  Home Team: {match.get('localteam', {}).get('@name')}")
                        print(f"  Away Team: {match.get('visitorteam', {}).get('@name')}")
                        print(f"  Home Score: {match.get('localteam', {}).get('@goals')}")
                        print(f"  Away Score: {match.get('visitorteam', {}).get('@goals')}")
                        
                        # Parse for settlement
                        event = service._parse_match_for_settlement(match, 'soccer', endpoint)
                        if event:
                            print(f"  Parsed Event: {event}")
                            print(f"  Is Completed: {event.get('is_completed')}")
                            print(f"  Is Cancelled: {event.get('is_cancelled')}")
                        return True
            else:
                print(f"❌ No data from {endpoint}")
        except Exception as e:
            print(f"❌ Error checking {endpoint}: {e}")
    
    print("\n❌ Target match not found in any endpoint")
    return False

if __name__ == "__main__":
    test_match_finding()
