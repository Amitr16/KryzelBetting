import json

# Read just the first part to understand structure
with open("Sports Pre Match/soccer/soccer_odds.json", 'r', encoding='utf-8') as f:
    # Read first 1000 characters to see structure
    first_part = f.read(1000)
    print("First 1000 characters:")
    print(first_part)
    print("\n" + "="*50 + "\n")
    
    # Reset file pointer
    f.seek(0)
    
    # Try to parse as JSON
    try:
        data = json.load(f)
        print("JSON structure:")
        print(f"Type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            if 'odds_data' in data:
                odds_data = data['odds_data']
                print(f"odds_data type: {type(odds_data)}")
                if isinstance(odds_data, dict):
                    print(f"odds_data keys: {list(odds_data.keys())[:10]}")  # First 10 keys
                    # Check first few values
                    for i, (key, value) in enumerate(list(odds_data.items())[:3]):
                        print(f"Key {i}: {key}")
                        print(f"Value type: {type(value)}")
                        if isinstance(value, dict):
                            print(f"Value keys: {list(value.keys())}")
                        print()
        elif isinstance(data, list):
            print(f"List length: {len(data)}")
            if len(data) > 0:
                print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
