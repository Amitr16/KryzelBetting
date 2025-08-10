#!/usr/bin/env python3
"""
Test combo bet sport and timing concatenation
"""

def create_combo_sport_timing(selections):
    """Create concatenated sport and timing strings for combo bets"""
    sports = []
    timings = []
    
    for selection in selections:
        if isinstance(selection, dict):
            sport = selection.get('sport_name', 'soccer')
            timing = selection.get('bet_timing', 'pregame')
        else:
            sport = 'soccer'
            timing = 'pregame'
        
        sports.append(sport)
        timings.append(timing)
    
    sport_string = '_'.join(sports)
    timing_string = '_'.join(timings)
    
    return sport_string, timing_string

def parse_combo_sport_timing(sport_string, timing_string):
    """Parse concatenated sport and timing strings for combo bets"""
    if not sport_string or not timing_string:
        return [], []
    
    sports = sport_string.split('_')
    timings = timing_string.split('_')
    
    # Ensure same length (pad with last value if needed)
    while len(timings) < len(sports):
        timings.append(timings[-1] if timings else 'pregame')
    
    while len(sports) < len(timings):
        sports.append(sports[-1] if sports else 'soccer')
    
    return sports, timings

# Test cases
test_selections = [
    [
        {
            "match_id": "6149386",
            "match_name": "Vasco vs CSA",
            "selection": "Vasco",
            "odds": 1.5,
            "sport_name": "soccer",
            "bet_timing": "pregame"
        },
        {
            "match_id": "341057",
            "match_name": "Chunichi Dragons vs Hanshin Tigers",
            "selection": "Hanshin Tigers",
            "odds": 1.62,
            "sport_name": "baseball",
            "bet_timing": "pregame"
        }
    ],
    [
        {
            "match_id": "12345",
            "match_name": "Lakers vs Warriors",
            "selection": "Lakers",
            "odds": 2.0,
            "sport_name": "bsktbl",
            "bet_timing": "pregame"
        },
        {
            "match_id": "67890",
            "match_name": "Manchester United vs Arsenal",
            "selection": "Manchester United",
            "odds": 1.8,
            "sport_name": "soccer",
            "bet_timing": "ingame"
        },
        {
            "match_id": "11111",
            "match_name": "Patriots vs Cowboys",
            "selection": "Patriots",
            "odds": 1.9,
            "sport_name": "football",
            "bet_timing": "pregame"
        }
    ]
]

print("🧪 TESTING COMBO SPORT/TIMING CONCATENATION")
print("=" * 60)

for i, selections in enumerate(test_selections, 1):
    print(f"\n📋 Test Case {i}: {len(selections)} selections")
    print("-" * 40)
    
    # Show individual selections
    for j, selection in enumerate(selections, 1):
        print(f"  Selection {j}:")
        print(f"    Match: {selection['match_name']}")
        print(f"    Sport: {selection['sport_name']}")
        print(f"    Timing: {selection['bet_timing']}")
    
    # Create concatenated strings
    sport_string, timing_string = create_combo_sport_timing(selections)
    print(f"\n  Combo Sport String: {sport_string}")
    print(f"  Combo Timing String: {timing_string}")
    
    # Parse back to individual values
    sports, timings = parse_combo_sport_timing(sport_string, timing_string)
    print(f"\n  Parsed Sports: {sports}")
    print(f"  Parsed Timings: {timings}")
    
    # Show settlement logic
    print(f"\n  Settlement Logic:")
    for k, (sport, timing) in enumerate(zip(sports, timings)):
        print(f"    Match {k+1} → Check {sport}/home and {sport}/d-1 endpoints")
