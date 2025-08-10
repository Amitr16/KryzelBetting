#!/usr/bin/env python3

from src.goalserve_client import OptimizedGoalServeClient
from src.bet_settlement_service import BetSettlementService

def test_settlement_direct():
    print("Testing settlement service directly...")
    
    # Create client and settlement service
    client = OptimizedGoalServeClient()
    settlement_service = BetSettlementService()
    
    # Test baseball historical data
    print("\n1. Testing baseball historical data...")
    baseball_data = client._make_request('baseball/d-1', use_cache=False)
    if baseball_data:
        print(f"Baseball data keys: {list(baseball_data.keys())}")
        
        # Extract matches
        matches = client._extract_matches_from_goalserve_data(baseball_data)
        print(f"Found {len(matches)} baseball matches")
        
        # Look for our specific teams
        target_teams = ['marines', 'hawks', 'dragons', 'tigers', 'eagles', 'buffaloes']
        for match in matches[:10]:  # Check first 10
            home_team = match.get('localteam', {}).get('name', '').lower()
            away_team = match.get('visitorteam', {}).get('name', '').lower()
            match_id = match.get('@id', 'Unknown')
            status = match.get('status', 'Unknown')
            
            if any(team in home_team or team in away_team for team in target_teams):
                print(f"*** FOUND RELEVANT MATCH ***")
                print(f"  Home: {match.get('localteam', {}).get('name', 'Unknown')}")
                print(f"  Away: {match.get('visitorteam', {}).get('name', 'Unknown')}")
                print(f"  ID: {match_id}")
                print(f"  Status: {status}")
                
                # Test parsing for settlement
                event = settlement_service._parse_match_for_settlement(match, 'baseball', 'baseball/d-1')
                if event:
                    print(f"  Parsed event: {event.get('id')} - {event.get('home_team')} vs {event.get('away_team')} - Completed: {event.get('is_completed')}")
                else:
                    print("  Failed to parse event")
    else:
        print("No baseball data found")
    
    # Test soccer historical data
    print("\n2. Testing soccer historical data...")
    soccer_data = client._make_request('soccer/d-1', use_cache=False)
    if soccer_data:
        print(f"Soccer data keys: {list(soccer_data.keys())}")
        matches = client._extract_matches_from_goalserve_data(soccer_data)
        print(f"Found {len(matches)} soccer matches")
    else:
        print("No soccer data found")

if __name__ == '__main__':
    test_settlement_direct()
