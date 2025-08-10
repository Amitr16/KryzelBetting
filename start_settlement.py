#!/usr/bin/env python3

import requests

def start_settlement():
    try:
        response = requests.post('http://localhost:5000/api/settlement/start')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    start_settlement()
