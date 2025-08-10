#!/usr/bin/env python3
"""
Extended Sport Detection for Individual Sports
Demonstrates how to determine sport from player names and match patterns
"""

def determine_sport_from_match_name(match_name):
    """Enhanced sport detection that handles both team sports and individual sports"""
    match_name_lower = match_name.lower()
    sports_to_check = set()
    
    # TEAM SPORTS (existing logic)
    # Baseball teams
    baseball_teams = ['marines', 'hawks', 'dragons', 'tigers', 'eagles', 'buffaloes', 
                     'giants', 'swallows', 'carp', 'baystars', 'lions', 'fighters', 'orix']
    if any(team in match_name_lower for team in baseball_teams):
        sports_to_check.add('baseball')
    
    # Basketball teams  
    basketball_teams = ['lakers', 'warriors', 'celtics', 'bulls', 'heat', 'knicks', 
                       'nets', 'raptors', 'mavericks', 'rockets', 'spurs', 'thunder']
    if any(team in match_name_lower for team in basketball_teams):
        sports_to_check.add('bsktbl')
    
    # Soccer teams
    soccer_teams = ['united', 'city', 'arsenal', 'chelsea', 'liverpool', 'barcelona', 
                   'real madrid', 'bayern', 'psg', 'juventus', 'milan', 'inter']
    if any(team in match_name_lower for team in soccer_teams):
        sports_to_check.add('soccer')
    
    # Football teams
    football_teams = ['patriots', 'cowboys', 'packers', 'steelers', '49ers', 'chiefs', 
                     'bills', 'ravens', 'eagles', 'giants', 'jets']
    if any(team in match_name_lower for team in football_teams):
        sports_to_check.add('football')
    
    # INDIVIDUAL SPORTS (new logic)
    # Tennis players - look for tennis-specific patterns
    tennis_indicators = [' vs ', ' vs. ', ' - ', ' vs ', ' vs. ']
    tennis_keywords = ['tennis', 'atp', 'wta', 'grand slam', 'open', 'championship']
    tennis_players = ['federer', 'nadal', 'djokovic', 'serena', 'venus', 'williams', 
                     'murray', 'wawrinka', 'thiem', 'medvedev', 'tsitsipas']
    
    if any(indicator in match_name_lower for indicator in tennis_indicators):
        if any(keyword in match_name_lower for keyword in tennis_keywords):
            sports_to_check.add('tennis')
        elif any(player in match_name_lower for player in tennis_players):
            sports_to_check.add('tennis')
        elif ' vs ' in match_name_lower and len(match_name_lower.split(' vs ')) == 2:
            # If it's "Player A vs Player B" format, likely tennis
            sports_to_check.add('tennis')
    
    # Boxing indicators
    boxing_keywords = ['boxing', 'fight', 'championship', 'title', 'weight', 'division']
    boxing_indicators = [' vs ', ' vs. ', ' vs ', ' vs. ']
    if any(keyword in match_name_lower for keyword in boxing_keywords):
        sports_to_check.add('boxing')
    elif ' vs ' in match_name_lower and any(word in match_name_lower for word in ['fight', 'boxing', 'champion']):
        sports_to_check.add('boxing')
    
    # Golf indicators
    golf_keywords = ['golf', 'pga', 'lpga', 'masters', 'open', 'championship', 'tournament']
    golf_players = ['woods', 'mickelson', 'mcilroy', 'spieth', 'thomas', 'dj', 'djokovic']
    if any(keyword in match_name_lower for keyword in golf_keywords):
        sports_to_check.add('golf')
    elif any(player in match_name_lower for player in golf_players):
        sports_to_check.add('golf')
    
    # MMA indicators
    mma_keywords = ['mma', 'ufc', 'bellator', 'fight', 'octagon', 'cage']
    if any(keyword in match_name_lower for keyword in mma_keywords):
        sports_to_check.add('mma')
    
    # Darts indicators
    darts_keywords = ['darts', 'pdc', 'bdo', 'world championship']
    darts_players = ['van gerwen', 'price', 'anderson', 'wright', 'cross']
    if any(keyword in match_name_lower for keyword in darts_keywords):
        sports_to_check.add('darts')
    elif any(player in match_name_lower for player in darts_players):
        sports_to_check.add('darts')
    
    # Table Tennis indicators
    table_tennis_keywords = ['table tennis', 'ping pong', 'ittf']
    if any(keyword in match_name_lower for keyword in table_tennis_keywords):
        sports_to_check.add('table_tennis')
    
    # Fallback logic
    if not sports_to_check:
        # If no specific sport identified, default to soccer
        sports_to_check.add('soccer')
    
    return list(sports_to_check)

# Example usage and testing
if __name__ == "__main__":
    test_matches = [
        # Team sports
        "Chiba Lotte Marines vs Fukuoka S. Hawks",
        "Los Angeles Lakers vs Golden State Warriors", 
        "Manchester United vs Manchester City",
        "New England Patriots vs Dallas Cowboys",
        
        # Individual sports
        "Roger Federer vs Rafael Nadal",
        "Serena Williams vs Venus Williams", 
        "Mike Tyson vs Evander Holyfield",
        "Tiger Woods vs Phil Mickelson",
        "Conor McGregor vs Khabib Nurmagomedov",
        "Michael van Gerwen vs Gerwyn Price",
        "Ma Long vs Fan Zhendong",
        
        # Ambiguous cases
        "Player A vs Player B",
        "Team Alpha vs Team Beta"
    ]
    
    print("🎯 SPORT DETECTION TESTING")
    print("=" * 50)
    
    for match in test_matches:
        sports = determine_sport_from_match_name(match)
        print(f"Match: {match}")
        print(f"Detected sports: {sports}")
        print("-" * 30)
