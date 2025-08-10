#!/usr/bin/env python3
"""
Test sport detection from match names
"""

def determine_sport_from_match_name(match_name):
    """Determine sport from match name patterns"""
    if not match_name:
        return 'soccer'  # Default fallback
    
    match_name_lower = match_name.lower()
    
    # Determine sport from match name patterns
    if any(team in match_name_lower for team in ['marines', 'hawks', 'dragons', 'tigers', 'eagles', 'buffaloes', 'giants', 'swallows', 'carp', 'baystars', 'lions', 'fighters', 'orix']):
        return 'baseball'
    elif any(team in match_name_lower for team in ['lakers', 'warriors', 'celtics', 'bulls', 'heat', 'knicks', 'nets', 'raptors', 'mavericks', 'rockets', 'spurs', 'thunder']):
        return 'bsktbl'
    elif any(team in match_name_lower for team in ['united', 'city', 'arsenal', 'chelsea', 'liverpool', 'barcelona', 'real madrid', 'bayern', 'psg', 'juventus', 'milan', 'inter', 'vasco', 'csa']):
        return 'soccer'
    elif any(team in match_name_lower for team in ['patriots', 'cowboys', 'packers', 'steelers', '49ers', 'chiefs', 'bills', 'ravens', 'eagles', 'giants', 'jets']):
        return 'football'
    else:
        # Default to soccer for unknown teams
        return 'soccer'

# Test cases
test_matches = [
    "Vasco vs CSA",
    "Chiba Lotte Marines vs Fukuoka S. Hawks", 
    "Chunichi Dragons vs Hanshin Tigers",
    "Lakers vs Warriors",
    "Manchester United vs Arsenal",
    "Patriots vs Cowboys",
    "Unknown Team A vs Unknown Team B"
]

print("🧪 TESTING SPORT DETECTION")
print("=" * 50)

for match_name in test_matches:
    sport = determine_sport_from_match_name(match_name)
    print(f"Match: {match_name}")
    print(f"Sport: {sport}")
    print("-" * 30)
