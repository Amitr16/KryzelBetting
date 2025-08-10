#!/usr/bin/env python3
"""
Script to test the settlement service directly and force settlement
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.bet_settlement_service import BetSettlementService
from src.main import app

def test_force_settlement():
    """Test the settlement service directly"""
    print("🔧 Testing Settlement Service Directly")
    print("=" * 50)
    
    # Create settlement service with Flask app
    service = BetSettlementService(app)
    
    # Start the service if not running
    if not service.running:
        print("🚀 Starting settlement service...")
        service.start()
    
    print(f"Service running: {service.running}")
    print(f"Total checks: {service.total_checks}")
    
    # Force check for completed matches
    print("\n🔍 Forcing check for completed matches...")
    service.check_for_completed_matches()
    
    print(f"\nAfter check:")
    print(f"  Total checks: {service.total_checks}")
    print(f"  Successful settlements: {service.successful_settlements}")
    print(f"  Failed settlements: {service.failed_settlements}")
    print(f"  Last error: {service.last_error}")
    
    # Check if the specific bet was settled
    with app.app_context():
        from src.models.betting import Bet
        
        # Check the specific bet
        bet = Bet.query.get(1)
        if bet:
            print(f"\n📋 Bet #1 Status:")
            print(f"  ID: {bet.id}")
            print(f"  Match: {bet.match_name}")
            print(f"  Status: {bet.status}")
            print(f"  Selection: {bet.selection}")
            print(f"  Stake: ${bet.stake}")
            print(f"  Potential Return: ${bet.potential_return}")
            print(f"  Actual Return: ${bet.actual_return}")
            print(f"  Settled At: {bet.settled_at}")
        else:
            print("❌ Bet #1 not found")
        
        # Check all pending bets
        pending_bets = Bet.query.filter_by(status='pending').all()
        print(f"\n📋 Pending bets after check: {len(pending_bets)}")
        for bet in pending_bets:
            print(f"  Bet {bet.id}: {bet.match_name} - {bet.selection}")

if __name__ == "__main__":
    test_force_settlement()
