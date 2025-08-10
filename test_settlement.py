#!/usr/bin/env python3

import requests
import time

def test_settlement():
    print("=== Testing Settlement Service ===")
    
    # 1. Check initial status
    print("\n1. Checking initial status...")
    response = requests.get('http://localhost:5000/api/settlement/status')
    print(f"Initial status: {response.json()}")
    
    # 2. Start the service
    print("\n2. Starting settlement service...")
    response = requests.post('http://localhost:5000/api/settlement/start')
    print(f"Start response: {response.json()}")
    
    # 3. Wait a moment
    print("\n3. Waiting 3 seconds...")
    time.sleep(3)
    
    # 4. Check status again
    print("\n4. Checking status after start...")
    response = requests.get('http://localhost:5000/api/settlement/status')
    data = response.json()
    print(f"Status after start: {data}")
    
    # 5. Wait for first check cycle
    print("\n5. Waiting for first check cycle (35 seconds)...")
    time.sleep(35)
    
    # 6. Check status after first cycle
    print("\n6. Checking status after first cycle...")
    response = requests.get('http://localhost:5000/api/settlement/status')
    data = response.json()
    print(f"Status after first cycle: {data}")

if __name__ == '__main__':
    test_settlement()
