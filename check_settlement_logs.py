#!/usr/bin/env python3
"""
Script to check settlement service logs and restart with better debugging
"""

import requests
import json
import time

def check_settlement_status():
    """Check current settlement service status"""
    try:
        response = requests.get('http://localhost:5000/api/settlement/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("🔍 Current Settlement Service Status:")
            print(f"  Service Running: {data.get('service_running', False)}")
            print(f"  Total Checks: {data.get('total_checks', 0)}")
            print(f"  Successful Settlements: {data.get('successful_settlements', 0)}")
            print(f"  Failed Settlements: {data.get('failed_settlements', 0)}")
            print(f"  Last Error: {data.get('last_error', 'None')}")
            print(f"  Pending Bets: {data.get('pending_bets', 0)}")
            return data
        else:
            print(f"❌ Error checking status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error connecting to settlement service: {e}")
        return None

def start_settlement_service():
    """Start the settlement service"""
    try:
        response = requests.post('http://localhost:5000/api/settlement/start', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Settlement service started: {data.get('status')}")
            return True
        else:
            print(f"❌ Error starting service: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error starting settlement service: {e}")
        return False

def monitor_settlement_service(duration_minutes=5):
    """Monitor the settlement service for a specified duration"""
    print(f"🔍 Monitoring settlement service for {duration_minutes} minutes...")
    
    start_time = time.time()
    check_interval = 10  # Check every 10 seconds
    
    while time.time() - start_time < duration_minutes * 60:
        status = check_settlement_status()
        
        if status and not status.get('service_running', False):
            print("❌ Settlement service stopped! Attempting to restart...")
            if start_settlement_service():
                print("✅ Service restarted successfully")
            else:
                print("❌ Failed to restart service")
                break
        
        time.sleep(check_interval)
    
    print("📊 Final status:")
    check_settlement_status()

if __name__ == "__main__":
    print("🔧 Settlement Service Debug Monitor")
    print("=" * 50)
    
    # Check current status
    check_settlement_status()
    
    # Start service if not running
    status = check_settlement_status()
    if not status or not status.get('service_running', False):
        print("\n🚀 Starting settlement service...")
        start_settlement_service()
    
    # Monitor for 5 minutes
    print("\n📊 Starting monitoring...")
    monitor_settlement_service(5)
