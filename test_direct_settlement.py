#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bet_settlement_service import BetSettlementService
from src.models.betting import Bet, User, db
from src.main import app

def test_direct_settlement():
    """Test the settlement logic directly"""
    
    with app.app_context():
        # Get the settlement service
        settlement_service = BetSettlementService()
        
        # Get the specific baseball bet
        bet = Bet.query.filter_by(match_id='341056').first()
        
        if bet:
            print(f"Found bet: {bet.match_name}")
            print(f"Match ID: {bet.match_id}")
            print(f"Status: {bet.status}")
            print(f"Selection: {bet.selection}")
            
            # Test finding the match in historical data
            match_event = settlement_service._find_match_in_historical_data('341056', bet.match_name)
            
            if match_event:
                print(f"✅ Found match in historical data:")
                print(f"  Home: {match_event['home_team']}")
                print(f"  Away: {match_event['away_team']}")
                print(f"  Home Score: {match_event['home_score']}")
                print(f"  Away Score: {match_event['away_score']}")
                print(f"  Status: {match_event['status']}")
                print(f"  Is Completed: {match_event['is_completed']}")
                
                # Test the bet outcome determination
                bet_won = settlement_service._determine_bet_outcome(bet, match_event, match_event['home_score'], match_event['away_score'])
                print(f"Bet won: {bet_won}")
                
                # Test auto-settlement
                print("Testing auto-settlement...")
                settlement_service._auto_settle_bets_for_match(match_event, [bet])
                
                # Check if bet was settled
                db.session.refresh(bet)
                print(f"Bet status after settlement: {bet.status}")
                print(f"Bet actual return: {bet.actual_return}")
                
            else:
                print("❌ Match not found in historical data")
        else:
            print("❌ Bet not found")

if __name__ == '__main__':
    test_direct_settlement()
