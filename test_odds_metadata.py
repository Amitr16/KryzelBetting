#!/usr/bin/env python3
"""
Test extracting sport information from odds data metadata
"""

def extract_sport_from_odds_data(odds_data):
    """Extract sport from odds data metadata"""
    try:
        if 'metadata' in odds_data and 'sport' in odds_data['metadata']:
            return odds_data['metadata']['sport']
        return None
    except Exception as e:
        print(f"Error extracting sport: {e}")
        return None

# Example odds data structure
example_odds_data = {
    "metadata": {
        "sport": "soccer",
        "display_name": "Soccer", 
        "icon": "⚽",
        "fetch_timestamp": "2025-08-08T06:02:41.304565",
        "date_range": ["07.08.2025", "09.08.2025"]
    },
    "odds_data": {
        "scores": {
            "sport": "soccer",
            "ts": "1754575246",
            "categories": [
                {
                    "name": "England: Championship",
                    "gid": "1205",
                    "matches": [
                        {
                            "id": "6149386",
                            "home_team": "Vasco",
                            "away_team": "CSA",
                            "odds": 1.5
                        }
                    ]
                }
            ]
        }
    }
}

print("🧪 TESTING SPORT EXTRACTION FROM ODDS DATA")
print("=" * 60)

# Extract sport from metadata
sport = extract_sport_from_odds_data(example_odds_data)
print(f"Extracted sport: {sport}")

# Show how frontend should send this to backend
print("\n📋 FRONTEND SHOULD SEND:")
print("=" * 40)
print("POST /api/betting/place")
print("{")
print('  "match_id": "6149386",')
print('  "match_name": "Vasco vs CSA",')
print('  "selection": "Vasco",')
print('  "odds": 1.5,')
print('  "stake": 10,')
print(f'  "sport_name": "{sport}",  // From odds data metadata')
print('  "bet_timing": "pregame"')
print("}")

print("\n📋 FOR COMBO BETS:")
print("=" * 40)
print("POST /api/betting/place-combo")
print("{")
print('  "selections": [')
print('    {')
print('      "match_id": "6149386",')
print('      "match_name": "Vasco vs CSA",')
print('      "selection": "Vasco",')
print('      "odds": 1.5,')
print(f'      "sport_name": "{sport}",  // From odds data metadata')
print('      "bet_timing": "pregame"')
print('    },')
print('    {')
print('      "match_id": "341057",')
print('      "match_name": "Chunichi Dragons vs Hanshin Tigers",')
print('      "selection": "Hanshin Tigers",')
print('      "odds": 1.62,')
print('      "sport_name": "baseball",  // From odds data metadata')
print('      "bet_timing": "pregame"')
print('    }')
print('  ],')
print('  "total_odds": 2.43,')
print('  "total_stake": 10')
print('  // Backend will create: sport_name="soccer_baseball", bet_timing="pregame_pregame"')
print("}")
