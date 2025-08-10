#!/usr/bin/env python3

import requests
import time

def restart_settlement():
    print("Restarting settlement service...")
    
    # Stop the service
    response = requests.post('http://localhost:5000/api/settlement/stop')
    print(f"Stop response: {response.json()}")
    
    # Wait a moment
    time.sleep(2)
    
    # Start the service
    response = requests.post('http://localhost:5000/api/settlement/start')
    print(f"Start response: {response.json()}")
    
    # Check status
    time.sleep(3)
    response = requests.get('http://localhost:5000/api/settlement/status')
    print(f"Status: {response.json()}")

if __name__ == '__main__':
    restart_settlement()
