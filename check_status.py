#!/usr/bin/env python3

import requests

def check_status():
    try:
        response = requests.get('http://localhost:5000/api/settlement/status')
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Service Running: {data.get('service_running')}")
        print(f"Pending Bets: {data.get('stats', {}).get('pending_bets')}")
        print(f"Total Checks: {data.get('stats', {}).get('total_checks')}")
        print(f"Successful Settlements: {data.get('stats', {}).get('successful_settlements')}")
        print(f"Failed Settlements: {data.get('stats', {}).get('failed_settlements')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_status()
