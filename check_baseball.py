#!/usr/bin/env python3

import requests

def check_baseball():
    try:
        response = requests.get('http://localhost:5000/api/sports/events/baseball')
        data = response.json()
        print(f'Baseball events: {len(data)}')
        
        for event in data[:10]:
            print(f'  {event["home_team"]} vs {event["away_team"]} - {event["status"]} - ID: {event["id"]}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    check_baseball()
