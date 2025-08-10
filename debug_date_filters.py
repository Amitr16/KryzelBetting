#!/usr/bin/env python3
"""
Debug script to test date filtering logic for Today and Tomorrow filters
"""

import json
from datetime import datetime, timedelta

def load_cricket_data():
    """Load cricket data to examine date formats"""
    try:
        with open('Sports Pre Match/cricket/cricket_odds.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading cricket data: {e}")
        return None

def extract_event_dates(data):
    """Extract all event dates from cricket data"""
    dates = []
    try:
        if 'odds_data' in data and 'scores' in data['odds_data']:
            category = data['odds_data']['scores'].get('category', [])
            if isinstance(category, list):
                for cat in category:
                    if 'matches' in cat and 'match' in cat['matches']:
                        match = cat['matches']['match']
                        if isinstance(match, list):
                            for m in match:
                                if 'date' in m:
                                    dates.append(m['date'])
                        elif isinstance(match, dict) and 'date' in match:
                            dates.append(match['date'])
            elif isinstance(category, dict):
                if 'matches' in category and 'match' in category['matches']:
                    match = category['matches']['match']
                    if isinstance(match, list):
                        for m in match:
                            if 'date' in m:
                                dates.append(m['date'])
                    elif isinstance(match, dict) and 'date' in match:
                        dates.append(match['date'])
    except Exception as e:
        print(f"Error extracting dates: {e}")
    
    return dates

def test_date_parsing():
    """Test the date parsing logic used in the filters"""
    print("=== Testing Date Parsing Logic ===")
    
    # Current date info
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    
    print(f"Current date: {now}")
    print(f"Today: {today}")
    print(f"Tomorrow: {tomorrow}")
    
    # Test the date parsing logic from the JavaScript filters
    test_dates = ["10.08.2025", "11.08.2025", "09.08.2025"]
    
    for date_str in test_dates:
        print(f"\nTesting date: {date_str}")
        
        try:
            # JavaScript equivalent logic
            if date_str and '.' in date_str:
                date_parts = date_str.split('.')
                if len(date_parts) == 3:
                    day = int(date_parts[0])
                    month = int(date_parts[1]) - 1  # Month is 0-indexed
                    year = int(date_parts[2])
                    event_date = datetime(year, month, day).date()
                    
                    print(f"  Parsed as: {event_date}")
                    print(f"  Is today: {event_date == today}")
                    print(f"  Is tomorrow: {event_date == tomorrow}")
                    
                    # Test the toDateString() equivalent
                    today_str = today.strftime('%Y-%m-%d')
                    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
                    event_str = event_date.strftime('%Y-%m-%d')
                    
                    print(f"  Today string: {today_str}")
                    print(f"  Tomorrow string: {tomorrow_str}")
                    print(f"  Event string: {event_str}")
                    print(f"  Matches today: {event_str == today_str}")
                    print(f"  Matches tomorrow: {event_str == tomorrow_str}")
                    
        except Exception as e:
            print(f"  Error parsing date: {e}")

def main():
    print("Debugging Date Filters for Today and Tomorrow")
    print("=" * 50)
    
    # Load cricket data
    data = load_cricket_data()
    if not data:
        print("Failed to load cricket data")
        return
    
    print("Cricket data loaded successfully")
    
    # Extract dates
    dates = extract_event_dates(data)
    print(f"\nFound {len(dates)} event dates:")
    for date in dates[:10]:  # Show first 10 dates
        print(f"  - {date}")
    
    if len(dates) > 10:
        print(f"  ... and {len(dates) - 10} more")
    
    # Test date parsing
    test_date_parsing()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check the output above for date parsing issues.")

if __name__ == "__main__":
    main()
