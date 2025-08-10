#!/usr/bin/env python3
"""
Script to test if the settlement service loop is actually running
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.bet_settlement_service import BetSettlementService
import time
import threading

def test_settlement_service():
    """Test the settlement service directly"""
    print("🔧 Testing Settlement Service Directly")
    print("=" * 50)
    
    # Create a new settlement service instance
    service = BetSettlementService()
    
    print(f"Initial state - Running: {service.running}")
    print(f"Thread: {service.settlement_thread}")
    
    # Start the service
    print("\n🚀 Starting settlement service...")
    success = service.start()
    print(f"Start result: {success}")
    print(f"Running after start: {service.running}")
    print(f"Thread after start: {service.settlement_thread}")
    print(f"Thread alive: {service.settlement_thread.is_alive() if service.settlement_thread else False}")
    
    # Monitor for a short time
    print("\n📊 Monitoring service for 60 seconds...")
    start_time = time.time()
    
    while time.time() - start_time < 60:
        print(f"Time: {time.time() - start_time:.1f}s - Running: {service.running}, Checks: {service.total_checks}")
        
        if service.settlement_thread:
            print(f"  Thread alive: {service.settlement_thread.is_alive()}")
            print(f"  Thread daemon: {service.settlement_thread.daemon}")
        
        if not service.running:
            print("❌ Service stopped running!")
            break
            
        time.sleep(5)  # Check every 5 seconds
    
    print(f"\n📊 Final status:")
    print(f"  Running: {service.running}")
    print(f"  Total Checks: {service.total_checks}")
    print(f"  Last Error: {service.last_error}")
    
    # Stop the service
    service.stop()
    print("✅ Service stopped")

if __name__ == "__main__":
    test_settlement_service()
