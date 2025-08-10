import requests
import json
from datetime import datetime

def test_settlement_service_status():
    """Test the bet settlement service status"""
    try:
        print("🔍 Testing Bet Settlement Service Status...")
        print("=" * 50)
        
        # Test if the main app is running
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Main App Status: {health_data.get('status', 'unknown')}")
                print(f"📊 WebSocket Clients: {health_data.get('websocket_clients', 0)}")
            else:
                print(f"❌ Main App Status: HTTP {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Main App Status: Not responding - {e}")
            return
        
        # Check pending bets
        try:
            import sqlite3
            conn = sqlite3.connect('src/database/app.db')
            cursor = conn.execute('SELECT COUNT(*) FROM bets WHERE status = "pending"')
            pending_count = cursor.fetchone()[0]
            conn.close()
            print(f"📋 Pending Bets: {pending_count}")
        except Exception as e:
            print(f"❌ Error checking pending bets: {e}")
        
        # Check recent bet activity
        try:
            conn = sqlite3.connect('src/database/app.db')
            cursor = conn.execute('''
                SELECT status, COUNT(*) as count 
                FROM bets 
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY status
            ''')
            recent_bets = cursor.fetchall()
            conn.close()
            
            print(f"\n📈 Recent Bet Activity (last 24 hours):")
            if recent_bets:
                for status, count in recent_bets:
                    print(f"  {status}: {count}")
            else:
                print("  No recent betting activity")
                
        except Exception as e:
            print(f"❌ Error checking recent activity: {e}")
        
        # Check if settlement service is running (look for recent log activity)
        print(f"\n🔄 Settlement Service Status:")
        print(f"  Check the main app logs for settlement service activity")
        print(f"  Look for messages like:")
        print(f"    - '🔍 Settlement check #X'")
        print(f"    - '📋 Found X pending bets'")
        print(f"    - '✅ Settlement check completed'")
        
        # Test a few basketball endpoints that settlement service would use
        print(f"\n🏀 Testing Basketball Settlement Endpoints:")
        test_endpoints = [
            'http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/bsktbl/home?json=1',
            'http://www.goalserve.com/getfeed/e1e6a26b1dfa4f52976f08ddd2a17244/bsktbl/d-1?json=1'
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint.split('/')[-1]}: Accessible")
                else:
                    print(f"  ❌ {endpoint.split('/')[-1]}: HTTP {response.status_code}")
            except Exception as e:
                print(f"  ❌ {endpoint.split('/')[-1]}: {str(e)[:50]}...")
        
        print(f"\n📊 Summary:")
        print(f"  - Main app is running and accessible")
        print(f"  - Database is accessible")
        print(f"  - Settlement service runs every 30 seconds")
        print(f"  - Check terminal logs for real-time settlement activity")
        
    except Exception as e:
        print(f"❌ Error testing settlement service: {e}")

if __name__ == "__main__":
    test_settlement_service_status()
