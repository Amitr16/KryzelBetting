#!/usr/bin/env python3
"""
Debug script to test settlement service
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bet_settlement_service import BetSettlementService
from src.models.betting import db, Bet
from src.main import app  # Import the Flask app directly
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_settlement():
    """Debug the settlement service"""
    try:
        # Initialize settlement service
        settlement_service = BetSettlementService()
        
        # Get pending bets using Flask app context
        with app.app_context():
            pending_bets = Bet.query.filter_by(status='pending').all()
            
            print(f"Found {len(pending_bets)} pending bets:")
            for bet in pending_bets:
                print(f"  - Match ID: {bet.match_id}, Match Name: {bet.match_name}, Sport: {bet.sport_name}")
            
            # Test the specific match we know is completed
            match_id = "6220376"
            match_name = "Adelaide Croatia Raiders vs Campbelltown City"
            sport_name = "soccer"
            
            print(f"\n🔍 Testing settlement for match {match_id}: {match_name}")
            
            # Test the GoalServe client
            print("Testing GoalServe API calls...")
            
            # Test soccernew/home endpoint
            home_data = settlement_service.client._make_request('soccernew/home', use_cache=False)
            if home_data:
                print("✅ Got data from soccernew/home")
                matches = settlement_service.client._extract_matches_from_goalserve_data(home_data)
                print(f"Found {len(matches)} matches in home data")
                
                # Look for our specific match
                found_match = None
                for match in matches:
                    if match.get('@id') == match_id:
                        found_match = match
                        break
                
                if found_match:
                    print(f"✅ Found match {match_id} in home data!")
                    print(f"Match status: {found_match.get('@status')}")
                    print(f"Home team: {found_match.get('localteam', {}).get('@name')}")
                    print(f"Away team: {found_match.get('visitorteam', {}).get('@name')}")
                    
                    # Parse for settlement
                    event = settlement_service._parse_match_for_settlement(found_match, sport_name, 'soccernew/home')
                    if event:
                        print(f"✅ Parsed match for settlement: {event}")
                        print(f"Is completed: {event.get('is_completed')}")
                        print(f"Home score: {event.get('home_score')}")
                        print(f"Away score: {event.get('away_score')}")
                    else:
                        print("❌ Failed to parse match for settlement")
                else:
                    print(f"❌ Match {match_id} not found in home data")
            else:
                print("❌ Failed to get data from soccernew/home")
            
            # Test historical data
            print("\nTesting historical data...")
            historical_data = settlement_service.client._make_request('soccernew/d-1', use_cache=False)
            if historical_data:
                print("✅ Got data from soccernew/d-1")
                matches = settlement_service.client._extract_matches_from_goalserve_data(historical_data)
                print(f"Found {len(matches)} matches in historical data")
                
                # Look for our specific match
                found_match = None
                for match in matches:
                    if match.get('@id') == match_id:
                        found_match = match
                        break
                
                if found_match:
                    print(f"✅ Found match {match_id} in historical data!")
                else:
                    print(f"❌ Match {match_id} not found in historical data")
            else:
                print("❌ Failed to get data from soccernew/d-1")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_settlement()
