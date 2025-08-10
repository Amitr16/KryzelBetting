#!/usr/bin/env python3
"""
Script to debug pending bets directly from the database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app
from src.models.betting import Bet, db
from datetime import datetime

def check_pending_bets():
    """Check pending bets directly from database"""
    with app.app_context():
        try:
            # Get all pending bets
            pending_bets = Bet.query.filter_by(status='pending').all()
            
            print(f"🔍 Found {len(pending_bets)} pending bets in database:")
            print("=" * 60)
            
            for i, bet in enumerate(pending_bets, 1):
                print(f"\n📋 Bet #{i}:")
                print(f"  ID: {bet.id}")
                print(f"  Match Name: {bet.match_name}")
                print(f"  Match ID: {bet.match_id}")
                print(f"  Sport: {bet.sport_name}")
                print(f"  Selection: {bet.selection}")
                print(f"  Stake: ${bet.stake}")
                print(f"  Potential Return: ${bet.potential_return}")
                print(f"  Bet Type: {bet.bet_type}")
                print(f"  Created At: {bet.created_at}")
                print(f"  User ID: {bet.user_id}")
                
                if bet.combo_selections:
                    print(f"  Combo Selections: {bet.combo_selections}")
                
                print("-" * 40)
            
            # Check if any bets have been settled recently
            recent_settled = Bet.query.filter(
                Bet.status.in_(['won', 'lost', 'void']),
                Bet.settled_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).all()
            
            if recent_settled:
                print(f"\n✅ Found {len(recent_settled)} bets settled today:")
                for bet in recent_settled:
                    print(f"  Bet {bet.id}: {bet.match_name} -> {bet.status} (${bet.actual_return})")
            else:
                print("\n📭 No bets settled today")
                
        except Exception as e:
            print(f"❌ Error checking database: {e}")
            import traceback
            traceback.print_exc()

def check_settlement_service_logs():
    """Check if we can access settlement service logs"""
    try:
        import requests
        response = requests.get('http://localhost:5000/api/settlement/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\n🔧 Settlement Service Status:")
            print(f"  Running: {data.get('service_running', False)}")
            print(f"  Total Checks: {data.get('total_checks', 0)}")
            print(f"  Last Check: {data.get('last_check_time', 'Never')}")
            print(f"  Last Error: {data.get('last_error', 'None')}")
            
            # Get stats if available
            stats = data.get('stats', {})
            print(f"  Pending Bets (from API): {stats.get('pending_bets', 'Unknown')}")
            print(f"  Successful Settlements: {stats.get('successful_settlements', 0)}")
            print(f"  Failed Settlements: {stats.get('failed_settlements', 0)}")
        else:
            print(f"❌ Error getting settlement status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking settlement service: {e}")

if __name__ == "__main__":
    print("🔍 Debug Pending Bets")
    print("=" * 60)
    
    check_pending_bets()
    check_settlement_service_logs()
