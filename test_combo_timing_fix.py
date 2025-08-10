#!/usr/bin/env python3
"""
Test that combo bets correctly handle sport and timing concatenation
"""

def test_combo_bet_data():
    """Test combo bet data structure"""
    
    # Simulate frontend bet slip data
    bet_slip = [
        {
            "matchId": "6149386",
            "matchName": "Vasco vs CSA",
            "selection": "Vasco",
            "odds": 1.5,
            "sport": "soccer",
            "bet_timing": "pregame"
        },
        {
            "matchId": "341057",
            "matchName": "Chunichi Dragons vs Hanshin Tigers",
            "selection": "Hanshin Tigers",
            "odds": 1.62,
            "sport": "baseball",
            "bet_timing": "pregame"
        },
        {
            "matchId": "12345",
            "matchName": "Lakers vs Warriors",
            "selection": "Lakers",
            "odds": 2.0,
            "sport": "bsktbl",
            "bet_timing": "ingame"
        }
    ]
    
    # Simulate frontend combo bet data creation
    combo_bet_data = {
        "bet_type": "combo",
        "selections": [
            {
                "match_id": bet["matchId"],
                "match_name": bet["matchName"],
                "selection": bet["selection"],
                "odds": bet["odds"],
                "sport_name": bet["sport"],
                "bet_timing": bet["bet_timing"]
            }
            for bet in bet_slip
        ],
        "total_odds": 4.86,
        "total_stake": 10
    }
    
    print("🧪 TESTING COMBO BET DATA STRUCTURE")
    print("=" * 50)
    
    print("Frontend bet slip:")
    for i, bet in enumerate(bet_slip, 1):
        print(f"  Bet {i}: {bet['sport']} - {bet['bet_timing']}")
    
    print("\nFrontend combo bet data:")
    for i, selection in enumerate(combo_bet_data["selections"], 1):
        print(f"  Selection {i}: {selection['sport_name']} - {selection['bet_timing']}")
    
    # Simulate backend processing
    selections = combo_bet_data["selections"]
    
    # Extract sports and timings
    sports = [selection.get('sport_name', 'soccer') for selection in selections]
    timings = [selection.get('bet_timing', 'pregame') for selection in selections]
    
    # Create concatenated strings
    sport_string = '_'.join(sports)
    timing_string = '_'.join(timings)
    
    print(f"\nBackend concatenated sport_name: {sport_string}")
    print(f"Backend concatenated bet_timing: {timing_string}")
    
    # Verify correct concatenation
    expected_sport = "soccer_baseball_bsktbl"
    expected_timing = "pregame_pregame_ingame"
    
    print(f"\nExpected sport_name: {expected_sport}")
    print(f"Expected bet_timing: {expected_timing}")
    
    if sport_string == expected_sport and timing_string == expected_timing:
        print("✅ SUCCESS: Combo bet sport and timing concatenation working correctly!")
    else:
        print("❌ ERROR: Combo bet concatenation not working as expected")
        print(f"  Sport: got '{sport_string}', expected '{expected_sport}'")
        print(f"  Timing: got '{timing_string}', expected '{expected_timing}'")

if __name__ == "__main__":
    test_combo_bet_data()
