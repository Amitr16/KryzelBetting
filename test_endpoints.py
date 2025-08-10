#!/usr/bin/env python3

import requests

def test_endpoints():
    endpoints = [
        'baseballnew/d-1',
        'baseballnew/d-2', 
        'soccernew/d-1',
        'soccernew/d-2',
        'basketballnew/d-1',
        'basketballnew/d-2'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:5000/api/sports/{endpoint}')
            print(f'{endpoint}: {response.status_code}')
            if response.status_code == 200:
                data = response.json()
                print(f'  Data keys: {list(data.keys()) if isinstance(data, dict) else "Not a dict"}')
        except Exception as e:
            print(f'{endpoint}: Error - {e}')

if __name__ == '__main__':
    test_endpoints()
