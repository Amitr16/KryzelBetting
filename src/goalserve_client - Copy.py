"""
Working GoalServe API Client with Correct Data Structure Parsing
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedGoalServeClient:
    def __init__(self):
        self.base_url = "http://www.goalserve.com/getfeed"
        self.access_token = "e1e6a26b1dfa4f52976f08ddd2a17244"
        
        # Cache configuration
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache
        self.cache_lock = threading.Lock()
        
        # Request configuration for faster responses
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GoalServe-Client/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Timeout settings
        self.timeout = (5, 15)  # (connect_timeout, read_timeout)
        
        # Sports configuration with working endpoints
        self.sports_config = {
            'soccer': {
                'endpoint': 'soccernew/home',
                'events_endpoint': 'soccernew/home',
                'icon': '⚽',
                'display_name': 'Soccer',
                'has_draw': True,
                'priority': 1
            },
            'basketball': {
                'endpoint': 'bsktbl/home',
                'events_endpoint': 'bsktbl/home', 
                'icon': '🏀',
                'display_name': 'Basketball',
                'has_draw': False,
                'priority': 2
            },
            'tennis': {
                'endpoint': 'tennis_scores/home',
                'events_endpoint': 'tennis_scores/home',
                'icon': '🎾', 
                'display_name': 'Tennis',
                'has_draw': False,
                'priority': 3
            },
            'baseball': {
                'endpoint': 'baseball/home',
                'events_endpoint': 'baseball/home',
                'icon': '⚾',
                'display_name': 'Baseball', 
                'has_draw': False,
                'priority': 4
            },
            'hockey': {
                'endpoint': 'hockey/home',
                'events_endpoint': 'hockey/home',
                'icon': '🏒',
                'display_name': 'Hockey',
                'has_draw': False,
                'priority': 5
            }
        }

    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for request"""
        params_str = json.dumps(params or {}, sort_keys=True)
        return f"{endpoint}:{params_str}"

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        cache_time = cache_entry.get('timestamp', 0)
        return time.time() - cache_time < self.cache_duration

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        with self.cache_lock:
            cache_entry = self.cache.get(cache_key)
            if self._is_cache_valid(cache_entry):
                logger.info(f"Cache hit for {cache_key}")
                return cache_entry['data']
        return None

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set data in cache"""
        with self.cache_lock:
            self.cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }

    def _make_request(self, endpoint: str, params: Dict = None, use_cache: bool = True) -> Optional[Dict]:
        """Make optimized API request with caching"""
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data

        # Build URL
        url = f"{self.base_url}/{self.access_token}/{endpoint}"
        if not params:
            params = {}
        params['json'] = '1'  # Always request JSON format

        try:
            logger.info(f"Making API call to: {url}")
            start_time = time.time()
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            elapsed_time = time.time() - start_time
            logger.info(f"API call completed in {elapsed_time:.2f} seconds")
            
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}")
                return None

            # Parse response
            try:
                # Check if response is XML (common for GoalServe)
                content_type = response.headers.get('content-type', '').lower()
                if 'xml' in content_type or response.text.strip().startswith('<?xml'):
                    logger.info("Detected XML response, converting to JSON")
                    # For now, return None for XML responses since we need JSON
                    # TODO: Implement XML to JSON conversion if needed
                    return None
                
                # Handle UTF-8 BOM if present
                text = response.text
                if text.startswith('\ufeff'):
                    text = text[1:]  # Remove BOM
                
                data = json.loads(text)
                logger.info("Parsed JSON response successfully")
                
                # Cache the result
                if use_cache:
                    self._set_cache(cache_key, data)
                
                return data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def get_available_sports(self) -> List[Dict]:
        """Get available sports with fast parallel loading"""
        logger.info("Getting available sports with parallel loading...")
        
        # Check cache for sports list
        cache_key = "available_sports"
        cached_sports = self._get_from_cache(cache_key)
        if cached_sports:
            return cached_sports

        sports_data = []
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit requests for high-priority sports first
            future_to_sport = {}
            
            # Start with top 3 sports for faster initial load
            priority_sports = sorted(
                self.sports_config.items(), 
                key=lambda x: x[1]['priority']
            )[:3]
            
            for sport_name, config in priority_sports:
                future = executor.submit(self._get_sport_event_count, sport_name, config)
                future_to_sport[future] = (sport_name, config)
            
            # Process completed requests
            for future in as_completed(future_to_sport, timeout=30):
                sport_name, config = future_to_sport[future]
                try:
                    event_count = future.result()
                    sports_data.append({
                        'name': sport_name,
                        'display_name': config['display_name'],
                        'icon': config['icon'],
                        'event_count': event_count
                    })
                    logger.info(f"Loaded {sport_name}: {event_count} events")
                except Exception as e:
                    logger.error(f"Failed to load {sport_name}: {e}")
                    # Add with 0 events as fallback
                    sports_data.append({
                        'name': sport_name,
                        'display_name': config['display_name'],
                        'icon': config['icon'],
                        'event_count': 0
                    })

        # Sort by priority
        sports_data.sort(key=lambda x: next(
            (config['priority'] for name, config in self.sports_config.items() 
             if name == x['name']), 999
        ))

        # Cache the result
        self._set_cache(cache_key, sports_data)
        
        logger.info(f"Loaded {len(sports_data)} sports")
        return sports_data

    def _get_sport_event_count(self, sport_name: str, config: Dict) -> int:
        """Get event count for a specific sport (only active matches)"""
        try:
            data = self._make_request(config['endpoint'], use_cache=True)
            if not data:
                return 0
            
            # Extract matches from the data using correct structure
            matches = self._extract_matches_from_goalserve_data(data)
            
            # Parse matches and count only active (non-completed, non-cancelled) ones
            active_count = 0
            for match in matches:
                try:
                    event = self._parse_single_event(match, sport_name, config)
                    if event and not event.get('is_completed', False) and not event.get('is_cancelled', False):
                        active_count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse match for count: {e}")
                    continue
            
            return active_count
            
        except Exception as e:
            logger.error(f"Error getting event count for {sport_name}: {e}")
            return 0

    def _extract_matches_from_goalserve_data(self, data: Dict) -> List[Dict]:
        """Extract matches from GoalServe API response data using correct structure"""
        matches = []
        
        try:
            if not isinstance(data, dict):
                return matches
            
            logger.info(f"Extracting matches from GoalServe data with keys: {list(data.keys())}")
            
            # GoalServe structure: { "scores": { "category": [...] } }
            if 'scores' in data and isinstance(data['scores'], dict):
                scores = data['scores']
                
                if 'category' in scores:
                    categories = scores['category']
                    
                    # Handle both single category (dict) and multiple categories (list)
                    if isinstance(categories, dict):
                        categories = [categories]
                    
                    if isinstance(categories, list):
                        logger.info(f"Found {len(categories)} categories")
                        
                        for category in categories:
                            if isinstance(category, dict):
                                category_name = category.get('@name', 'Unknown League')
                                
                                # Handle different sports data structures
                                # Soccer: category -> matches -> match
                                # Basketball/Tennis: category -> match (direct)
                                if 'matches' in category:
                                    # Soccer structure
                                    matches_container = category['matches']
                                    if isinstance(matches_container, dict) and 'match' in matches_container:
                                        category_matches = matches_container['match']
                                        self._process_matches(category_matches, category_name, matches)
                                elif 'match' in category:
                                    # Basketball/Tennis structure
                                    category_matches = category['match']
                                    self._process_matches(category_matches, category_name, matches)
            
            logger.info(f"Total matches extracted: {len(matches)}")
            
        except Exception as e:
            logger.error(f"Error extracting matches: {e}")
        
        return matches

    def _process_matches(self, category_matches, category_name: str, matches: List[Dict]):
        """Helper method to process matches from a category"""
        if isinstance(category_matches, dict):
            # Single match
            category_matches['@category_name'] = category_name
            matches.append(category_matches)
        elif isinstance(category_matches, list):
            # Multiple matches
            for match in category_matches:
                match['@category_name'] = category_name
            matches.extend(category_matches)
        
        match_count = len(category_matches) if isinstance(category_matches, list) else 1
        logger.info(f"Category '{category_name}': {match_count} matches")

    def get_sport_events(self, sport_name: str, date_filter: str = 'all', limit: int = 50) -> List[Dict]:
        """Get sport events with real odds data using filters to reduce feed size"""
        logger.info(f"Getting events for {sport_name} (limit: {limit})")
        
        # Get sport configuration
        config = self.sports_config.get(sport_name, {})
        if not config:
            logger.warning(f"No configuration found for sport: {sport_name}")
            return []
        
        try:
            # Add filter parameters to reduce feed size as suggested by GoalServe tech
            params = {
                'limit': str(limit),  # Limit number of matches
                'showodds': '1'       # Include odds data
            }
            
            # Get fresh data from API with filters
            data = self._make_request(config['events_endpoint'], params=params, use_cache=False)  # Don't use cache for events
            
            if not data:
                logger.warning(f"No data received for {sport_name}")
                return []

            # Extract matches from the data using correct structure
            matches = self._extract_matches_from_goalserve_data(data)
            logger.info(f"Extracted {len(matches)} raw matches for {sport_name}")
            
            # Get odds data for this sport (if available)
            odds_data = self.get_prematch_odds(sport_name)
            odds_matches = {}
            
            if odds_data and 'scores' in odds_data:
                # Extract odds matches
                scores = odds_data['scores']
                if 'category' in scores:
                    categories = scores['category']
                    if isinstance(categories, list):
                        for category in categories:
                            if 'matches' in category and 'match' in category['matches']:
                                matches_list = category['matches']['match']
                                if isinstance(matches_list, list):
                                    for match in matches_list:
                                        match_id = match.get('id')
                                        if match_id:
                                            odds_matches[match_id] = match
                                elif isinstance(matches_list, dict):
                                    match_id = matches_list.get('id')
                                    if match_id:
                                        odds_matches[match_id] = matches_list
            
            logger.info(f"Found {len(odds_matches)} matches with odds data")
            
            # Parse matches into events
            events = []
            for i, match in enumerate(matches[:limit]):
                try:
                    event = self._parse_single_event(match, sport_name, config)
                    if event:
                        # Try to merge odds data
                        match_id = event.get('id')
                        if match_id and match_id in odds_matches:
                            odds_match = odds_matches[match_id]
                            event = self._merge_odds_data(event, odds_match)
                        
                        events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to parse match {i}: {e}")
                    continue
            
            # Filter out old completed matches with unknown scores
            filtered_events = []
            for event in events:
                is_old_match = False
                
                # Check if match has a date
                date_str = event.get('date', '')
                time_str = event.get('time', '')
                
                if date_str:
                    try:
                        # Parse the date (format: "Aug 05" or "05.08.2025")
                        from datetime import datetime
                        current_year = datetime.now().year
                        
                        if '.' in date_str:
                            # Format: "05.08.2025"
                            match_date = datetime.strptime(date_str, '%d.%m.%Y')
                        else:
                            # Format: "Aug 05" - assume current year
                            match_date = datetime.strptime(f"{date_str} {current_year}", "%b %d %Y")
                        
                        # Parse the time if it's in HH:MM format
                        if ':' in time_str and len(time_str.split(':')) == 2:
                            try:
                                hour, minute = map(int, time_str.split(':'))
                                # Combine date and time
                                match_datetime = match_date.replace(hour=hour, minute=minute)
                                
                                # If match datetime is more than 24 hours in the past, mark as old
                                time_diff = datetime.now() - match_datetime
                                if time_diff.total_seconds() > 86400:  # 24 hours in seconds
                                    is_old_match = True
                                    event['is_completed'] = True
                                    logger.debug(f"Marked old match as completed: {event['home_team']} vs {event['away_team']} (date: {date_str}, time: {time_str})")
                                else:
                                    logger.debug(f"Match within 24 hours, keeping: {event['home_team']} vs {event['away_team']} (date: {date_str}, time: {time_str})")
                            except ValueError:
                                # If time parsing fails, fall back to date-only check
                                if (datetime.now() - match_date).days > 2:  # More lenient: 2 days instead of 1
                                    is_old_match = True
                                    event['is_completed'] = True
                                    logger.debug(f"Marked old match as completed: {event['home_team']} vs {event['away_team']} (date: {date_str})")
                        else:
                            # No time info, fall back to date-only check
                            if (datetime.now() - match_date).days > 2:  # More lenient: 2 days instead of 1
                                is_old_match = True
                                event['is_completed'] = True
                                logger.debug(f"Marked old match as completed: {event['home_team']} vs {event['away_team']} (date: {date_str})")
                    except ValueError:
                        # If date parsing fails, don't filter out - keep the match
                        logger.debug(f"Could not parse date '{date_str}' for {event['home_team']} vs {event['away_team']}")
                        is_old_match = False
                
                if not is_old_match:
                    filtered_events.append(event)
            
            logger.info(f"Successfully parsed {len(events)} events for {sport_name}, filtered to {len(filtered_events)} active events")
            return filtered_events
            
        except Exception as e:
            logger.error(f"Error getting events for {sport_name}: {e}")
            return []
    
    def _merge_odds_data(self, event: Dict, odds_match: Dict) -> Dict:
        """Merge odds data from odds feed into event data"""
        try:
            if 'odds' in odds_match:
                odds_data = odds_match['odds']
                if isinstance(odds_data, dict):
                    # Extract odds from the complex GoalServe structure
                    odds_1 = None
                    odds_x = None
                    odds_2 = None
                    
                    # Look for match winner odds in the type array (using exact logic from working script)
                    if 'type' in odds_data:
                        types = odds_data['type']
                        if isinstance(types, list):
                            for type_data in types:
                                if isinstance(type_data, dict):
                                    market_name = type_data.get('value', '')
                                    bookmakers = type_data.get('bookmaker', [])
                                    
                                    if isinstance(bookmakers, list):
                                        # Look for bet365 specifically (exact logic from working script)
                                        for bookmaker in bookmakers:
                                            bookie_name = bookmaker.get('name', '').lower()
                                            if bookie_name == 'bet365':
                                                odds_list = bookmaker.get('odd', [])
                                                if isinstance(odds_list, list):
                                                    for odd in odds_list:
                                                        name = odd.get('name', '')
                                                        value = odd.get('value', '')
                                                        # Only extract Home/Away odds for match winner
                                                        if market_name == 'Home/Away':
                                                            if name == 'Home':
                                                                odds_1 = float(value) if value else None
                                                            elif name == 'Away':
                                                                odds_2 = float(value) if value else None
                                                        elif market_name == '1X2':
                                                            if name == '1':
                                                                odds_1 = float(value) if value else None
                                                            elif name == 'X':
                                                                odds_x = float(value) if value else None
                                                            elif name == '2':
                                                                odds_2 = float(value) if value else None
                                                break  # Found bet365, stop looking
                    
                    # Update event with real odds
                    if odds_1 or odds_2 or odds_x:
                        event['odds_1'] = odds_1
                        event['odds_x'] = odds_x
                        event['odds_2'] = odds_2
                        logger.debug(f"Merged real odds for {event.get('home_team', '')} vs {event.get('away_team', '')}: 1={odds_1}, X={odds_x}, 2={odds_2}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error merging odds data: {e}")
            return event

    def _parse_single_event(self, match: Dict, sport_name: str, config: Dict) -> Optional[Dict]:
        """Parse a single event from match data using GoalServe format"""
        try:
            # Extract team/player names based on sport structure
            home_team = 'Unknown Home'
            away_team = 'Unknown Away'
            
            if sport_name == 'tennis':
                # Tennis structure: player array with @name attributes (exact logic from working script)
                players = match.get('player', [])
                if not isinstance(players, list) or len(players) != 2:
                    logger.debug(f"Skipping match with {len(players) if isinstance(players, list) else 'non-list'} players")
                    return None
                
                home_team = players[0].get('@name', 'Unknown Home')  # Use '@name' as per tennis structure
                away_team = players[1].get('@name', 'Unknown Away')  # Use '@name' as per tennis structure
            else:
                # Soccer/Basketball structure: localteam/awayteam or localteam/visitorteam
                # Try both @name and name attributes for different sports
                home_team = (match.get('localteam', {}).get('@name') or 
                           match.get('localteam', {}).get('name', 'Unknown Home'))
                away_team = (match.get('awayteam', {}).get('@name') or 
                           match.get('awayteam', {}).get('name', 'Unknown Away'))
                
                # Fallback for soccer structure (visitorteam)
                if away_team == 'Unknown Away':
                    away_team = (match.get('visitorteam', {}).get('@name') or 
                               match.get('visitorteam', {}).get('name', 'Unknown Away'))
            
            if not home_team or not away_team or home_team == 'Unknown Home' or away_team == 'Unknown Away':
                logger.warning(f"Could not extract team names from match")
                return None

            # Extract time and status using @ attributes
            time_str = match.get('@time', '') or match.get('@status', '') or 'TBD'
            date_str = match.get('@date', '') or match.get('@formatted_date', '') or datetime.now().strftime('%b %d')
            status = match.get('@status', time_str)
            
            # Detect if match is live based on status (filter for "Not Started" like working script)
            is_live = False
            is_completed = False
            is_cancelled = False
            
            # Only process "Not Started" matches (like working script)
            if status != "Not Started":
                logger.debug(f"Skipping match with status: {status}")
                return None
            
            if status and status.isdigit():
                status_code = int(status)
                # Status codes like "22", "63" indicate live matches (minute of the game)
                is_live = status_code > 0 and status_code <= 90
                # Status codes like "90" might indicate completed matches (end of regulation)
                is_completed = status_code > 90
            elif status and 'timer' in match:
                # If there's a timer, it's likely live
                is_live = bool(match.get('@timer', ''))
            elif status == "FT":
                # Full Time indicates completed matches
                is_completed = True
            elif status == "90":
                # Minute 90 could be live or completed - check if there's a timer
                if match.get('@timer', ''):
                    is_live = True
                else:
                    is_completed = True
            elif status == "HT":
                # Half Time indicates live match
                is_live = True
            elif status in ["Cancl.", "Postp.", "WO"]:
                # Cancelled, Postponed, or Walk Over matches
                is_cancelled = True
            elif ":" in status:
                # Time format like "14:30" indicates scheduled match (not live, not completed)
                is_live = False
                is_completed = False
            
            # Extract scores based on sport
            home_score = '?'
            away_score = '?'
            
            if sport_name == 'tennis':
                # Tennis: extract scores from player arrays
                players = match.get('player', [])
                if isinstance(players, list) and len(players) >= 2:
                    home_score = players[0].get('@totalscore', '?')
                    away_score = players[1].get('@totalscore', '?')
            else:
                # Soccer/Basketball: extract from team objects
                # Try both @goals/@totalscore and goals/totalscore for different sports
                home_score = (match.get('localteam', {}).get('@goals') or 
                            match.get('localteam', {}).get('@totalscore') or
                            match.get('localteam', {}).get('goals') or
                            match.get('localteam', {}).get('totalscore', '?'))
                away_score = (match.get('awayteam', {}).get('@goals') or 
                            match.get('awayteam', {}).get('@totalscore') or
                            match.get('awayteam', {}).get('goals') or
                            match.get('awayteam', {}).get('totalscore', '?'))
                
                # Fallback for soccer structure (visitorteam)
                if away_score == '?':
                    away_score = (match.get('visitorteam', {}).get('@goals') or 
                                match.get('visitorteam', {}).get('@totalscore') or
                                match.get('visitorteam', {}).get('goals') or
                                match.get('visitorteam', {}).get('totalscore', '?'))
            
            # Extract venue
            venue = match.get('@venue', '')
            
            # Extract match ID
            match_id = match.get('@id', f"{sport_name}_{hash(f'{home_team}_{away_team}_{time_str}')}")
            
            # Generate realistic odds based on sport
            odds = self._generate_odds_for_sport(sport_name, config)
            
            # Extract league from category context
            league = match.get('@category_name', '') or match.get('category', {}).get('@name', '') or "Unknown League"

            # Extract odds if available
            odds_1 = None
            odds_x = None
            odds_2 = None
            
            # Look for odds in the match data (now using real GoalServe odds)
            if 'odds' in match:
                odds_data = match['odds']
                if isinstance(odds_data, dict):
                    # Extract odds from the complex GoalServe structure
                    odds_1 = None
                    odds_x = None
                    odds_2 = None
                    
                    # Look for match winner odds in the type array
                    if 'type' in odds_data:
                        types = odds_data['type']
                        if isinstance(types, list):
                            for type_data in types:
                                if isinstance(type_data, dict):
                                    # Look for "Home/Away" or "1X2" type odds
                                    value = type_data.get('value', '')
                                    if 'Home/Away' in value or '1X2' in value:
                                        if 'bookmaker' in type_data:
                                            bookmakers = type_data['bookmaker']
                                            if isinstance(bookmakers, list) and bookmakers:
                                                # Use the first bookmaker's odds
                                                first_bookmaker = bookmakers[0]
                                                if 'odd' in first_bookmaker:
                                                    odds_list = first_bookmaker['odd']
                                                    if isinstance(odds_list, list):
                                                        for odd in odds_list:
                                                            name = odd.get('name', '')
                                                            value = odd.get('value', '')
                                                            if name == 'Home' or name == '1':
                                                                odds_1 = float(value) if value else None
                                                            elif name == 'Away' or name == '2':
                                                                odds_2 = float(value) if value else None
                                                            elif name == 'X' or name == 'Draw':
                                                                odds_x = float(value) if value else None
                    
                    # If we found odds, use them
                    if odds_1 or odds_2 or odds_x:
                        logger.debug(f"Found real odds for {match.get('@home', '')} vs {match.get('@away', '')}: 1={odds_1}, X={odds_x}, 2={odds_2}")
            
            # For now, since soccer odds endpoint is not working, we'll set these to None
            # This can be updated when soccer odds become available
            
            # Create event object
            event = {
                'id': match.get('@id', ''),
                'home_team': home_team,
                'away_team': away_team,
                'time': time_str,
                'date': date_str,
                'status': status,
                'home_score': home_score,
                'away_score': away_score,
                'venue': match.get('@venue', ''),
                'league': match.get('@category_name', ''),
                'is_live': is_live,
                'is_completed': is_completed,
                'is_cancelled': is_cancelled,
                'odds_1': odds_1,
                'odds_x': odds_x,
                'odds_2': odds_2,
                'sport': sport_name
            }
            
            logger.info(f"Successfully parsed event: {home_team} vs {away_team} at {time_str}")
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None

    def _generate_odds_for_sport(self, sport_name: str, config: Dict) -> Dict:
        """Return actual odds from GoalServe API, or empty if none available"""
        # Only return actual odds from GoalServe, no random generation
        return {}

    def get_prematch_odds(self, sport_name: str) -> Dict:
        """Fetch pre-match odds from GoalServe API - using exact working approach"""
        try:
            # Map sport names to GoalServe category codes
            sport_categories = {
                'soccer': 'soccer_10',
                'basketball': 'basket_10', 
                'tennis': 'tennis_10',
                'baseball': 'baseball_10',
                'cricket': 'cricket_10',
                'hockey': 'hockey_10',
                'football': 'football_10',
                'handball': 'handball_10',
                'volleyball': 'volleyball_10',
                'rugby': 'rugby_10',
                'boxing': 'boxing_10',
                'mma': 'mma_10',
                'esports': 'esports_10',
                'golf': 'golf_10',
                'darts': 'darts_10',
                'futsal': 'futsal_10',
                'table_tennis': 'table_tennis_10',
                'rugbyleague': 'rugbyleague_10'
            }
            
            category = sport_categories.get(sport_name)
            if not category:
                logger.warning(f"No odds category found for sport: {sport_name}")
                return {}
            
            # Skip soccer as it's not working
            if sport_name == 'soccer':
                logger.info(f"Skipping soccer odds (endpoint not working)")
                return {}
            
            # Use the exact same URL format as the working script
            url = f"https://www.goalserve.com/getfeed/{self.access_token}/getodds/soccer?cat={category}&json=1&bm=16"
            
            # Fetch odds using the exact same approach as working script
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    odds_data = response.json()
                    logger.info(f"Successfully fetched odds for {sport_name}")
                    return odds_data
                else:
                    logger.warning(f"HTTP {response.status_code} for {sport_name}")
                    return {}
                    
            except Exception as e:
                logger.error(f"Error fetching odds for {sport_name}: {e}")
                return {}
            
        except Exception as e:
            logger.error(f"Error fetching odds for {sport_name}: {e}")
            return {}

    def get_live_odds(self, sport_name: str) -> List[Dict]:
        """Get live odds for a specific sport using GoalServe's inplay-mapping endpoint"""
        logger.info(f"Fetching live odds for {sport_name}")
        
        if sport_name not in self.sports_config:
            logger.warning(f"Unknown sport: {sport_name}")
            return []
        
        config = self.sports_config[sport_name]
        
        # Map sport names to GoalServe inplay-mapping endpoints
        inplay_endpoints = {
            'soccer': 'soccernew/inplay-mapping',
            'basketball': 'basketball/inplay-mapping', 
            'tennis': 'tennis_scores/inplay-mapping',
            'baseball': 'baseball/inplay-mapping',
            'hockey': 'hockey/inplay-mapping'
        }
        
        endpoint = inplay_endpoints.get(sport_name)
        if not endpoint:
            logger.warning(f"No inplay-mapping endpoint found for {sport_name}")
            return []
        
        try:
            # Fetch inplay-mapping data
            mapping_data = self._make_request(endpoint, use_cache=False)  # Don't cache live data
            
            if not mapping_data:
                logger.warning(f"No inplay-mapping data received for {sport_name}")
                return []
            
            # Get current live matches from the regular feed
            live_matches = self._get_live_matches_from_regular_feed(sport_name)
            
            # Combine mapping data with live match data to create live odds
            live_odds = self._create_live_odds_from_mapping(mapping_data, live_matches, sport_name, config)
            
            logger.info(f"Successfully fetched live odds for {len(live_odds)} matches")
            return live_odds
            
        except Exception as e:
            logger.error(f"Error fetching live odds for {sport_name}: {e}")
            return []

    def _get_live_matches_from_regular_feed(self, sport_name: str) -> List[Dict]:
        """Get live matches from the regular GoalServe feed"""
        try:
            config = self.sports_config[sport_name]
            data = self._make_request(config['endpoint'], use_cache=False)
            
            if not data:
                return []
            
            matches = self._extract_matches_from_goalserve_data(data)
            live_matches = []
            
            for match in matches:
                status = match.get('@status', '')
                if self._is_match_live(status, match):
                    live_matches.append(match)
            
            return live_matches
            
        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return []

    def _create_live_odds_from_mapping(self, mapping_data: Dict, live_matches: List[Dict], sport_name: str, config: Dict) -> List[Dict]:
        """Create live odds by combining mapping data with live match data"""
        live_odds = []
        
        try:
            # Extract mapping information
            mappings = mapping_data.get('mappings', {}).get('match', [])
            if not isinstance(mappings, list):
                mappings = [mappings] if mappings else []
            
            # Create a lookup for live matches
            live_matches_lookup = {}
            for match in live_matches:
                match_id = match.get('@id', '')
                home_team = match.get('localteam', {}).get('@name', '')
                away_team = match.get('visitorteam', {}).get('@name', '')
                key = f"{home_team}_{away_team}"
                live_matches_lookup[key] = match
            
            # First, try to match mappings with live matches
            matched_mappings = set()
            for mapping in mappings:
                try:
                    inplay_team1 = mapping.get('@inplay_team1_id', '')
                    inplay_team2 = mapping.get('@inplay_team2_id', '')
                    
                    # Find corresponding live match with improved matching
                    live_match = None
                    for key, match in live_matches_lookup.items():
                        home_team = match.get('localteam', {}).get('@name', '')
                        away_team = match.get('visitorteam', {}).get('@name', '')
                        
                        # Try multiple matching strategies
                        match_found = False
                        
                        # Strategy 1: Exact match
                        if (inplay_team1.lower() == home_team.lower() and 
                            inplay_team2.lower() == away_team.lower()):
                            match_found = True
                        
                        # Strategy 2: Partial match (one team name contains the other)
                        elif (inplay_team1.lower() in home_team.lower() or 
                              home_team.lower() in inplay_team1.lower() or
                              inplay_team2.lower() in away_team.lower() or
                              away_team.lower() in inplay_team2.lower()):
                            match_found = True
                        
                        # Strategy 3: Word-based matching (for cases like "Congo" vs "Congo Republic")
                        elif (any(word in home_team.lower() for word in inplay_team1.lower().split()) or
                              any(word in away_team.lower() for word in inplay_team2.lower().split())):
                            match_found = True
                        
                        if match_found:
                            live_match = match
                            break
                    
                    if live_match:
                        # Generate live odds for this match
                        live_odds_data = self._generate_dynamic_live_odds(live_match, sport_name)
                        
                        live_odds.append({
                            'match_id': live_match.get('@id', ''),
                            'pregame_match_id': mapping.get('@pregame_match_id', ''),
                            'inplay_match_id': mapping.get('@inplay_match_id', ''),
                            'home_team': live_match.get('localteam', {}).get('@name', ''),
                            'away_team': live_match.get('visitorteam', {}).get('@name', ''),
                            'home_score': live_match.get('localteam', {}).get('@goals', '0'),
                            'away_score': live_match.get('visitorteam', {}).get('@goals', '0'),
                            'status': live_match.get('@status', ''),
                            'time': live_match.get('@time', ''),
                            'venue': live_match.get('@venue', ''),
                            'league': live_match.get('@category_name', ''),
                            'live_odds': live_odds_data,
                            'sport': sport_name,
                            'team1_kit_color': mapping.get('team1_kit_color', {}).get('@value', ''),
                            'team2_kit_color': mapping.get('team2_kit_color', {}).get('@value', '')
                        })
                        matched_mappings.add(live_match.get('@id', ''))
                        
                except Exception as e:
                    logger.warning(f"Failed to process mapping: {e}")
                    continue
            
            # Now generate live odds for ALL live matches that weren't matched
            for match in live_matches:
                match_id = match.get('@id', '')
                if match_id not in matched_mappings:
                    # Generate live odds for this match
                    live_odds_data = self._generate_dynamic_live_odds(match, sport_name)
                    
                    live_odds.append({
                        'match_id': match.get('@id', ''),
                        'pregame_match_id': '',
                        'inplay_match_id': '',
                        'home_team': match.get('localteam', {}).get('@name', ''),
                        'away_team': match.get('visitorteam', {}).get('@name', ''),
                        'home_score': match.get('localteam', {}).get('@goals', '0'),
                        'away_score': match.get('visitorteam', {}).get('@goals', '0'),
                        'status': match.get('@status', ''),
                        'time': match.get('@time', ''),
                        'venue': match.get('@venue', ''),
                        'league': match.get('@category_name', ''),
                        'live_odds': live_odds_data,
                        'sport': sport_name,
                        'team1_kit_color': '',
                        'team2_kit_color': ''
                    })
            
            logger.info(f"Created live odds for {len(live_odds)} matches")
            
        except Exception as e:
            logger.error(f"Error creating live odds from mapping: {e}")
        
        return live_odds

    def _generate_dynamic_live_odds(self, match: Dict, sport_name: str) -> Dict:
        """Fetch actual live odds from GoalServe inplay endpoint"""
        try:
            # Get the inplay match ID from the match data
            inplay_match_id = match.get('@id', '')
            if not inplay_match_id:
                return {}
            
            # Fetch live odds from the inplay endpoint
            inplay_data = self._make_request(f'soccernew/inplay/{inplay_match_id}', use_cache=False)
            if not inplay_data or 'scores' not in inplay_data:
                return {}
            
            # Extract odds from the inplay data
            match_data = inplay_data['scores'].get('match', {})
            if not match_data:
                return {}
            
            # Look for odds in the match data
            odds = self._extract_live_odds_from_match(match_data, sport_name)
            return odds
            
        except Exception as e:
            logger.warning(f"Failed to fetch live odds for match {match.get('@id', '')}: {e}")
            return {}

    def _is_match_live(self, status: str, match: Dict) -> bool:
        """Check if a match is currently live based on status and timer"""
        if not status:
            return False
        
        # Check for live status indicators
        if status.isdigit():
            status_code = int(status)
            return status_code > 0 and status_code <= 90
        elif status in ["HT", "1H", "2H"]:
            return True
        elif status == "90" and match.get('@timer', ''):
            return True
        elif ":" in status and not status.startswith("FT"):
            # Time format like "14:30" - check if it's current time
            return False  # Scheduled match, not live
        
        return False

    def _extract_live_odds_from_match(self, match: Dict, sport_name: str) -> Dict:
        """Extract live odds from match data"""
        live_odds = {}
        
        try:
            # Look for odds data in the match structure
            # GoalServe might include odds in different formats
            odds_sources = [
                match.get('odds', {}),
                match.get('betting', {}),
                match.get('markets', {}),
                match.get('live_odds', {})
            ]
            
            for odds_source in odds_sources:
                if isinstance(odds_source, dict) and odds_source:
                    # Extract different types of odds
                    live_odds.update(self._parse_odds_markets(odds_source, sport_name))
            
            # Only return actual odds from GoalServe, no random generation
            return live_odds
            
        except Exception as e:
            logger.warning(f"Error extracting live odds: {e}")
            return {}

    def _parse_odds_markets(self, odds_data: Dict, sport_name: str) -> Dict:
        """Parse different types of odds markets from GoalServe data"""
        markets = {}
        
        try:
            # Common odds market types
            market_types = {
                '1x2': ['1', 'x', '2'],
                'match_winner': ['home', 'draw', 'away'],
                'total_goals': ['over', 'under'],
                'both_teams_score': ['yes', 'no'],
                'double_chance': ['1x', '12', 'x2']
            }
            
            for market_type, selections in market_types.items():
                if market_type in odds_data:
                    market_odds = odds_data[market_type]
                    if isinstance(market_odds, dict):
                        markets[market_type] = market_odds
                    elif isinstance(market_odds, list):
                        markets[market_type] = dict(zip(selections, market_odds))
            
        except Exception as e:
            logger.warning(f"Error parsing odds markets: {e}")
        
        return markets

    def _generate_live_odds_based_on_score(self, match: Dict, sport_name: str) -> Dict:
        """Return actual odds from GoalServe API, or empty if none available"""
        # Only return actual odds from GoalServe, no random generation
        return {}

    def clear_cache(self):
        """Clear all cached data"""
        with self.cache_lock:
            self.cache.clear()
        logger.info("Cache cleared")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with self.cache_lock:
            total_entries = len(self.cache)
            valid_entries = sum(1 for entry in self.cache.values() if self._is_cache_valid(entry))
            
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'cache_duration': self.cache_duration
        }

