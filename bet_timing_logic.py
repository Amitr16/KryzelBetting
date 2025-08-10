#!/usr/bin/env python3
"""
Bet Timing Logic: How to determine pregame vs ingame bets
"""

from datetime import datetime, timedelta
import re

def determine_bet_timing(match_status, match_time, current_time=None):
    """
    Determine if a bet is pregame or ingame based on match status and time
    
    Args:
        match_status (str): Match status from API (e.g., "Not Started", "Live", "45", "HT")
        match_time (str): Match time (e.g., "14:30", "15:45")
        current_time (datetime): Current time (defaults to now)
    
    Returns:
        str: "pregame" or "ingame"
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Convert match_time to datetime for comparison
    try:
        # Parse match time (assuming format like "14:30")
        if ':' in match_time:
            hour, minute = map(int, match_time.split(':'))
            match_datetime = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            # If no time format, assume it's a status
            match_datetime = current_time
    except:
        match_datetime = current_time
    
    # Pregame indicators
    pregame_statuses = [
        "Not Started", "Scheduled", "TBD", "Postponed", "Cancelled",
        "NS", "TBD", "Postp.", "Cancl."
    ]
    
    # Ingame indicators
    ingame_statuses = [
        "Live", "1H", "2H", "HT", "ET", "PEN", "AET",
        "1st Half", "2nd Half", "Extra Time", "Penalties"
    ]
    
    # Check status first (most reliable)
    if match_status in pregame_statuses:
        return "pregame"
    elif match_status in ingame_statuses:
        return "ingame"
    
    # Check if status is a number (minute of game)
    if match_status.isdigit():
        minute = int(match_status)
        if 1 <= minute <= 90:  # Soccer: 1-90 minutes
            return "ingame"
        elif minute > 90:  # Extra time
            return "ingame"
        else:
            return "pregame"
    
    # Check time-based logic
    time_diff = abs((current_time - match_datetime).total_seconds())
    
    # If match time is more than 30 minutes in the future = pregame
    if time_diff > 1800:  # 30 minutes
        return "pregame"
    # If match time is within 30 minutes or in the past = ingame
    else:
        return "ingame"

def test_bet_timing_logic():
    """Test the bet timing logic with various scenarios"""
    
    test_cases = [
        # (match_status, match_time, expected_result, description)
        ("Not Started", "15:30", "pregame", "Match not started yet"),
        ("Live", "15:30", "ingame", "Match is live"),
        ("45", "15:30", "ingame", "45th minute of game"),
        ("HT", "15:30", "ingame", "Half time"),
        ("90", "15:30", "ingame", "90th minute"),
        ("120", "15:30", "ingame", "Extra time"),
        ("Scheduled", "16:00", "pregame", "Scheduled match"),
        ("TBD", "TBD", "pregame", "Time to be determined"),
        ("Postponed", "15:30", "pregame", "Postponed match"),
        ("1H", "15:30", "ingame", "First half"),
        ("2H", "15:30", "ingame", "Second half"),
        ("ET", "15:30", "ingame", "Extra time"),
        ("PEN", "15:30", "ingame", "Penalties"),
    ]
    
    print("🧪 TESTING BET TIMING LOGIC")
    print("=" * 50)
    
    for status, time, expected, description in test_cases:
        result = determine_bet_timing(status, time)
        status_icon = "✅" if result == expected else "❌"
        print(f"{status_icon} {status:12} | {time:8} | {result:8} | {description}")
    
    print("\n📝 LOGIC SUMMARY:")
    print("Pregame (bet_timing = 'pregame'):")
    print("  - Status: Not Started, Scheduled, TBD, Postponed")
    print("  - Time: More than 30 minutes in future")
    print("  - Example: Bet placed 2 hours before match")
    print()
    print("Ingame (bet_timing = 'ingame'):")
    print("  - Status: Live, 1H, 2H, HT, ET, PEN, or minute numbers (1-120)")
    print("  - Time: Within 30 minutes or during match")
    print("  - Example: Bet placed while match is running")

def show_implementation_example():
    """Show how to implement this in the betting system"""
    print("\n🔧 IMPLEMENTATION EXAMPLE:")
    print("=" * 50)
    
    print("""
    # In your betting route (src/routes/betting.py):
    
    @betting_bp.route('/place', methods=['POST'])
    @token_required
    def place_bet():
        # ... existing code ...
        
        # Get match data from API
        match_data = get_match_data(match_id)
        match_status = match_data.get('status', 'Not Started')
        match_time = match_data.get('time', 'TBD')
        
        # Determine bet timing
        bet_timing = determine_bet_timing(match_status, match_time)
        
        # Create bet with timing
        bet = Bet(
            user_id=user.id,
            match_id=match_id,
            match_name=match_name,
            selection=selection,
            odds=odds,
            stake=stake,
            potential_return=stake * odds,
            sport_name=sport_name,
            bet_timing=bet_timing,  # Add this!
            status='pending'
        )
        
        # Log for analytics
        logger.info(f"Bet placed: {bet_timing} bet on {match_name}")
    """)

if __name__ == "__main__":
    test_bet_timing_logic()
    show_implementation_example()
