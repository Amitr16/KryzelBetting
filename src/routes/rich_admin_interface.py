"""
Rich Admin Interface - Extracted from original admin_app.py with tenant filtering
"""

from flask import Blueprint, request, session, redirect, render_template_string, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
import os

rich_admin_bp = Blueprint('rich_admin', __name__)

# Fix database path to work from root directory
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src', 'database', 'app.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_event_financials(event_id, market_id, sport_name, operator_id):
    """Calculate max liability and max possible gain for a specific event+market combination for a specific operator"""
    try:
        conn = get_db_connection()
        
        # Get all pending bets for this specific event+market combination from this operator's users
        query = """
        SELECT b.bet_selection, b.stake, b.potential_return, b.odds
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE b.match_id = ? AND b.market = ? AND b.sport_name = ? AND b.status = 'pending'
        AND u.sportsbook_operator_id = ?
        """
        
        bets = conn.execute(query, (event_id, market_id, sport_name, operator_id)).fetchall()
        conn.close()
        
        if not bets:
            return 0.0, 0.0  # No bets = no liability or gain
        
        # Group bets by selection (outcome)
        selections = {}
        total_stakes = 0
        
        for bet in bets:
            selection = bet['bet_selection']
            stake = float(bet['stake'])
            potential_return = float(bet['potential_return'])
            
            if selection not in selections:
                selections[selection] = {'total_stake': 0, 'total_payout': 0}
            
            selections[selection]['total_stake'] += stake
            selections[selection]['total_payout'] += potential_return
            total_stakes += stake
        
        # Calculate profit/loss for each possible outcome
        outcomes = []
        for selection, data in selections.items():
            # If this selection wins: pay out winners, keep losing stakes
            payout = data['total_payout']
            profit_loss = total_stakes - payout
            outcomes.append(profit_loss)
        
        # Max liability = worst case (most negative outcome)
        max_liability = abs(min(outcomes)) if outcomes else 0.0
        
        # Max possible gain = best case (most positive outcome)  
        max_possible_gain = max(outcomes) if outcomes else 0.0
        
        return max_liability, max_possible_gain
        
    except Exception as e:
        print(f"Error calculating financials: {e}")
        return 0.0, 0.0

def calculate_total_revenue(operator_id):
    """Calculate total revenue from settled bets for a specific operator"""
    try:
        conn = get_db_connection()
        
        # Calculate revenue from settled bets for this operator's users
        # Revenue = Total stakes from losing bets - Total payouts to winning bets
        query = """
        SELECT 
            SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) as total_stakes_lost,
            SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as total_payouts_won
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE b.status IN ('won', 'lost') AND u.sportsbook_operator_id = ?
        """
        
        result = conn.execute(query, (operator_id,)).fetchone()
        conn.close()
        
        total_stakes_lost = result['total_stakes_lost'] or 0
        total_payouts_won = result['total_payouts_won'] or 0
        
        # Revenue = Money kept from losing bets - Extra money paid to winners
        total_revenue = total_stakes_lost - total_payouts_won
        
        return total_revenue
        
    except Exception as e:
        print(f"Error calculating total revenue: {e}")
        return 0.0

def get_operator_from_session():
    """Get operator info from session"""
    print(f"🔍 DEBUG: Session data: {session}")
    print(f"🔍 DEBUG: operator_id in session: {session.get('operator_id')}")
    print(f"🔍 DEBUG: operator_subdomain in session: {session.get('operator_subdomain')}")
    
    # Check for new session keys first, fall back to old ones for backward compatibility
    operator_id = session.get('operator_id') or session.get('admin_id')
    operator_subdomain = session.get('operator_subdomain') or session.get('admin_subdomain')
    
    if not operator_id:
        print("❌ DEBUG: No operator_id or admin_id in session")
        return None
    
    conn = get_db_connection()
    operator = conn.execute("""
        SELECT id, sportsbook_name, login, subdomain, email
        FROM sportsbook_operators 
        WHERE id = ?
    """, (operator_id,)).fetchone()
    conn.close()
    
    print(f"🔍 DEBUG: Operator found: {operator}")
    return dict(operator) if operator else None

def serve_rich_admin_template(subdomain):
    """Serve rich admin template for a specific subdomain"""
    # Check if admin is logged in using new session keys, fall back to old ones
    operator_id = session.get('operator_id') or session.get('admin_id')
    operator_subdomain = session.get('operator_subdomain') or session.get('admin_subdomain')
    
    if not operator_id or operator_subdomain != subdomain:
        return redirect(f'/{subdomain}/admin/login')
    
    operator = get_operator_from_session()
    if not operator:
        return redirect(f'/{subdomain}/admin/login')
    
    # Render the rich admin template with operator branding
    return render_template_string(RICH_ADMIN_TEMPLATE, operator=operator)

@rich_admin_bp.route('/<subdomain>/admin')
@rich_admin_bp.route('/<subdomain>/admin/')
def rich_admin_dashboard(subdomain):
    """Rich admin dashboard with tenant filtering"""
    return serve_rich_admin_template(subdomain)

@rich_admin_bp.route('/<subdomain>/admin/api/betting-events')
def get_tenant_betting_events(subdomain):
    """Get betting events filtered by tenant"""
    print(f"🔍 DEBUG: get_tenant_betting_events called for subdomain: {subdomain}")
    
    # Get operator from session
    operator = get_operator_from_session()
    if not operator:
        print(f"🔍 DEBUG: No operator found in session")
        return jsonify({'error': 'Unauthorized'}), 401
    
    print(f"🔍 DEBUG: Operator found: {operator['id']} ({operator['subdomain']})")
    
    try:
        import os
        import json
        
        # Get database connection for checking disabled events
        print(f"🔍 DEBUG: Getting database connection...")
        conn = get_db_connection()
        print(f"🔍 DEBUG: Database connection established")
        
        # Path to Sports Pre Match directory - use absolute path from project root
        sports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Sports Pre Match')
        print(f"🔍 DEBUG: Sports directory path: {sports_dir}")
        
        all_events = []
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get filter and search parameters
        sport_filter = request.args.get('sport', '')
        market_filter = request.args.get('market', '')
        search_query = request.args.get('search', '').lower()
        sort_by = request.args.get('sort_by', 'event_id')
        sort_order = request.args.get('sort_order', 'asc')
        show_only_with_bets = request.args.get('show_only_with_bets', 'false', type=str).lower() == 'true'
        
        print(f"🔍 DEBUG: Query params - page: {page}, per_page: {per_page}, sort_by: {sort_by}, sort_order: {sort_order}")
        print(f"🔍 DEBUG: Filters - sport: {sport_filter}, market: {market_filter}, search: {search_query}")
        print(f"🔍 DEBUG: show_only_with_bets: {show_only_with_bets}")
        
        # First, query the database to find which event_market combinations have bets
        if show_only_with_bets:
            print(f"🔍 DEBUG: Querying database for events with bets...")
            # Get events with bets from database first
            bet_events_query = """
                SELECT DISTINCT b.match_id, b.sport_name, b.market, COUNT(*) as bet_count
                FROM bets b 
                JOIN users u ON b.user_id = u.id 
                WHERE u.sportsbook_operator_id = ?
                GROUP BY b.match_id, b.sport_name, b.market
                HAVING COUNT(*) > 0
                ORDER BY bet_count DESC
            """
            print(f"🔍 DEBUG: Executing SQL query with operator_id: {operator['id']}")
            bet_events_result = conn.execute(bet_events_query, (operator['id'],)).fetchall()
            print(f"🔍 DEBUG: Found {len(bet_events_result)} event_market combinations with bets")
            
            # Create a set of events to load - convert all to strings for consistent matching
            events_to_load = set()
            for row in bet_events_result:
                match_id = str(row['match_id'])
                sport_name = str(row['sport_name'])
                market_id = str(row['market'])
                events_to_load.add((match_id, sport_name, market_id))
                print(f"🔍 DEBUG: Added to events_to_load: ({match_id}, {sport_name}, {market_id})")
        else:
            # Load all events (slower)
            events_to_load = set()
            print(f"🔍 DEBUG: Loading all events (show_only_with_bets=False)")
        
        # Load sports and events data directly from JSON files to avoid HTTP loops
        import os
        import json
        
        print(f"🔍 DEBUG: Looking for sports directory: {sports_dir}")
        if not os.path.exists(sports_dir):
            print(f"🔍 DEBUG: Sports directory not found: {sports_dir}")
            return jsonify({'error': 'Sports directory not found'})
        
        print(f"🔍 DEBUG: Sports directory found, starting to load events...")
        
        # Get all sports
        sports_data = {}
        all_events = []
        all_sports = set()
        all_markets = set()
        
        print(f"🔍 DEBUG: Starting to process sports folders...")
        
        try:
            # Load sports data
            sport_folders = [f for f in os.listdir(sports_dir) if os.path.isdir(os.path.join(sports_dir, f))]
            print(f"🔍 DEBUG: Found sport folders: {sport_folders}")
            
            for sport_folder in sport_folders:
                sport_path = os.path.join(sports_dir, sport_folder)
                sports_data[sport_folder] = {'display_name': sport_folder.title()}
                print(f"🔍 DEBUG: Processing sport folder: {sport_folder}")
                
                # Load events for this sport - files are named {sport}_odds.json
                events_file = os.path.join(sport_path, f'{sport_folder}_odds.json')
                print(f"🔍 DEBUG: Looking for events file: {events_file}")
                
                if os.path.exists(events_file):
                    print(f"🔍 DEBUG: Events file found, loading...")
                    try:
                        with open(events_file, 'r', encoding='utf-8') as f:
                            sport_data = json.load(f)
                        
                        print(f"🔍 DEBUG: JSON loaded, checking structure...")
                        print(f"🔍 DEBUG: Top level keys: {list(sport_data.keys())}")
                        
                        # Extract events from the JSON structure
                        sport_events = []
                        
                        # Handle different JSON structures for different sports
                        if 'odds_data' in sport_data and 'scores' in sport_data['odds_data']:
                            scores = sport_data['odds_data']['scores']
                            
                            # Check for categories (plural) - used by most sports
                            if 'categories' in scores:
                                print(f"🔍 DEBUG: Found odds_data.scores.categories structure")
                                for category in scores['categories']:
                                    if 'matches' in category:
                                        print(f"🔍 DEBUG: Category '{category.get('name', 'Unknown')}' has {len(category['matches'])} matches")
                                        # Add category info to each match for later use
                                        for match in category['matches']:
                                            match['_category_name'] = category.get('name', 'Unknown Category')
                                        sport_events.extend(category['matches'])
                            
                            # Check for category (singular) - used by cricket
                            elif 'category' in scores:
                                print(f"🔍 DEBUG: Found odds_data.scores.category structure (cricket)")
                                categories = scores['category']
                                if isinstance(categories, list):
                                    for category in categories:
                                        if 'matches' in category and 'match' in category['matches']:
                                            # Cricket has nested match structure
                                            match_data = category['matches']['match']
                                            if isinstance(match_data, dict):
                                                # Single match
                                                match_data['_category_name'] = category.get('name', 'Unknown Category')
                                                sport_events.append(match_data)
                                            elif isinstance(match_data, list):
                                                # Multiple matches
                                                for match in match_data:
                                                    match['_category_name'] = category.get('name', 'Unknown Category')
                                                sport_events.extend(match_data)
                                            print(f"🔍 DEBUG: Cricket category '{category.get('name', 'Unknown')}' has {len(sport_events)} matches")
                        else:
                            print(f"🔍 DEBUG: Unexpected JSON structure for {sport_folder}")
                            print(f"🔍 DEBUG: odds_data present: {'odds_data' in sport_data}")
                            if 'odds_data' in sport_data:
                                print(f"🔍 DEBUG: scores present: {'scores' in sport_data['odds_data']}")
                                if 'scores' in sport_data['odds_data']:
                                    scores = sport_data['odds_data']['scores']
                                    print(f"🔍 DEBUG: scores keys: {list(scores.keys())}")
                        
                        print(f"🔍 DEBUG: Loaded {len(sport_events)} events for {sport_folder}")
                        
                        # Process each event
                        for event in sport_events:
                            event_id = event.get('id', '')
                            sport_display_name = sports_data[sport_folder].get('display_name', sport_folder.title())
                            
                            # Process markets/odds
                            if 'odds' in event:
                                print(f"🔍 DEBUG: Processing odds for event {event_id}")
                                print(f"🔍 DEBUG: Odds structure: {list(event['odds'].keys())}")
                                
                                # Handle different odds structures for different sports
                                if sport_folder == 'cricket':
                                    # Cricket has odds.type[].bookmaker[].odd[] structure
                                    print(f"🔍 DEBUG: Processing cricket odds structure")
                                    if 'type' in event['odds']:
                                        for odd_type in event['odds']['type']:
                                            market_name = odd_type.get('value', '').lower()
                                            market_id = odd_type.get('id', '')
                                            
                                            if not market_id:
                                                print(f"🔍 DEBUG: No market ID found for {market_name} in cricket event {event_id}")
                                                continue
                                            
                                            # Extract odds values from bookmakers
                                            odds_values = []
                                            if 'bookmaker' in odd_type and odd_type['bookmaker']:
                                                for bookmaker in odd_type['bookmaker']:
                                                    if 'odd' in bookmaker:
                                                        for o in bookmaker['odd']:
                                                            value = o.get('value', '')
                                                            try:
                                                                float_val = float(value)
                                                                if float_val > 1.0:  # Valid odds
                                                                    odds_values.append(value)
                                                            except (ValueError, TypeError):
                                                                continue
                                            
                                            if not odds_values:
                                                print(f"🔍 DEBUG: No valid odds found for cricket market {market_name} in event {event_id}")
                                                continue
                                            
                                            # Process this cricket market
                                            self._process_cricket_market(event, event_id, sport_folder, market_id, market_name, odds_values, 
                                                                       all_sports, all_markets, events_to_load, show_only_with_bets, 
                                                                       betting_events, conn, operator_id, sport_display_name)
                                else:
                                    # Standard odds structure for other sports
                                    print(f"🔍 DEBUG: Processing standard odds structure for {sport_folder}")
                                    for odd in event['odds']:
                                        market_name = odd.get('value', '').lower()
                                        market_id = odd.get('id', '')
                                        
                                        if not market_id:
                                            print(f"🔍 DEBUG: No market ID found for {market_name} in event {event_id}")
                                            continue
                                        
                                        # Extract odds values from bookmakers
                                        odds_values = []
                                        if 'bookmakers' in odd and odd['bookmakers']:
                                            bookmaker = odd['bookmakers'][0]
                                            if 'odds' in bookmaker:
                                                for o in bookmaker['odds']:
                                                    value = o.get('value', '')
                                                    try:
                                                        float_val = float(value)
                                                        if float_val > 1.0:  # Valid odds
                                                            odds_values.append(value)
                                                    except (ValueError, TypeError):
                                                        continue
                                        
                                        if not odds_values:
                                            print(f"🔍 DEBUG: No valid odds found for market {market_name} in event {event_id}")
                                            continue
                                        
                                        # Process this standard market
                                        self._process_standard_market(event, event_id, sport_folder, market_id, market_name, odds_values,
                                                                   all_sports, all_markets, events_to_load, show_only_with_bets,
                                                                   betting_events, conn, operator_id, sport_display_name)
                                    
                                    # If we're only showing events with bets, check if this event_market has bets
                                    if show_only_with_bets:
                                        # Convert all to strings for consistent matching
                                        event_key = (str(event_id), str(sport_folder), str(market_id))
                                        print(f"🔍 DEBUG: Checking event_key: {event_key}")
                                        if event_key not in events_to_load:
                                            print(f"🔍 DEBUG: Skipping event {event_id} - not in events_to_load")
                                            continue  # Skip this event_market combination
                                        else:
                                            print(f"🔍 DEBUG: Found matching event {event_id} in events_to_load")
                                    
                                    # Add to sports and markets filters
                                    all_sports.add(sport_display_name)
                                    all_markets.add(market_name)
                                    
                                    # Create betting event entry with correct ID format: {event_id}_{market_id}
                                    betting_event = {
                                        'id': f"{event_id}_{market_id}",
                                        'unique_id': f"{event_id}_{market_id}",
                                        'event_id': f"{event_id}_{market_id}",
                                        'sport': sport_display_name,
                                        'event_name': f"{event.get('localteam', {}).get('name', 'Unknown')} vs {event.get('awayteam', {}).get('name', 'Unknown')}",
                                        'market': market_name,
                                        'market_display': market_name,
                                        'category': event.get('_category_name', 'Unknown Category'),
                                        'odds_data': odds_values,
                                        'is_active': True,
                                        'date': event.get('date', ''),
                                        'time': event.get('time', ''),
                                        'status': 'active' if event.get('status', 'Unknown').lower() != 'finished' else 'finished'
                                    }
                                    
                                    # Check if this event is disabled in the disabled_events table
                                    event_key = f"{event_id}_{market_id}"
                                    disabled_check = conn.execute(
                                        'SELECT * FROM disabled_events WHERE sport = ?', 
                                        (event_key,)
                                    ).fetchone()
                                    
                                    if disabled_check:
                                        betting_event['is_active'] = False
                                        betting_event['status'] = 'disabled'
                                    
                                    # Calculate financials for this event (tenant-filtered)
                                    # Use the actual market ID for database queries
                                    print(f"🔍 DEBUG: Calculating financials for event {event_id}, market {market_id}, sport {sport_folder}")
                                    max_liability, max_possible_gain = calculate_event_financials(event_id, market_id, sport_folder, operator['id'])
                                    betting_event['max_liability'] = max_liability
                                    betting_event['max_possible_gain'] = max_possible_gain
                                    
                                    # Add fields expected by the dashboard
                                    betting_event['name'] = f"{event.get('localteam', {}).get('name', 'Unknown')} vs {event.get('awayteam', {}).get('name', 'Unknown')}"
                                    betting_event['liability'] = max_liability
                                    betting_event['revenue'] = max_possible_gain
                                    
                                    # Get total bets for this event from the current operator's users
                                    print(f"🔍 DEBUG: Counting bets for event {event_id}, market {market_id}, sport {sport_folder}")
                                    bet_count_result = conn.execute("""
                                        SELECT COUNT(*) as count
                                        FROM bets b 
                                        JOIN users u ON b.user_id = u.id 
                                        WHERE u.sportsbook_operator_id = ? AND b.match_id = ? AND b.sport_name = ? AND b.market = ?
                                    """, (operator['id'], event_id, sport_folder, market_id)).fetchone()
                                    total_bets = bet_count_result['count'] if bet_count_result else 0
                                    betting_event['total_bets'] = total_bets
                                    
                                    all_events.append(betting_event)
                                    print(f"🔍 DEBUG: Added event {betting_event['id']} with {total_bets} bets")
                    except Exception as e:
                        print(f"🔍 DEBUG: Error loading events for {sport_folder}: {e}")
                        continue
        except Exception as e:
            print(f"🔍 DEBUG: Error processing sports directory: {e}")
            return jsonify({'error': f'Error processing sports directory: {e}'})


        
        # Apply filters after collecting all events
        filtered_events = all_events
        
        # Apply sport filter
        if sport_filter:
            filtered_events = [e for e in filtered_events if e['sport'].lower() == sport_filter.lower()]
        
        # Apply market filter
        if market_filter:
            filtered_events = [e for e in filtered_events if e['market'].lower() == market_filter.lower()]
        
        # Apply search filter
        if search_query:
            filtered_events = [e for e in filtered_events if search_query in e['event_name'].lower()]
        
        # Sort events
        reverse = sort_order.lower() == 'desc'
        if sort_by == 'event_id':
            filtered_events.sort(key=lambda x: int(x['event_id'].split('_')[0]) if x['event_id'].split('_')[0].isdigit() else 0, reverse=reverse)
        elif sort_by == 'sport':
            filtered_events.sort(key=lambda x: x['sport'], reverse=reverse)
        elif sort_by == 'event_name':
            filtered_events.sort(key=lambda x: x['event_name'], reverse=reverse)
        elif sort_by == 'market':
            filtered_events.sort(key=lambda x: x['market'], reverse=reverse)
        elif sort_by == 'max_liability':
            filtered_events.sort(key=lambda x: x.get('max_liability', 0), reverse=reverse)
        elif sort_by == 'max_possible_gain':
            filtered_events.sort(key=lambda x: x.get('max_possible_gain', 0), reverse=reverse)
        elif sort_by == 'status':
            filtered_events.sort(key=lambda x: x.get('is_active', True), reverse=reverse)
        
        # Apply pagination
        total_events = len(filtered_events)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_events = filtered_events[start_idx:end_idx]
        
        # Get unique sports and markets for filters (from all events, not filtered)
        unique_sports = list(all_sports)
        unique_markets = list(all_markets)
        
        # Calculate summary statistics (from filtered events)
        active_events = len([e for e in filtered_events if e.get('is_active', True)])
        total_liability = sum(e.get('max_liability', 0) for e in filtered_events)
        total_revenue = calculate_total_revenue(operator['id'])  # Calculate from settled bets for this operator
        
        # Debug logging
        print(f"🔍 DEBUG: Total events loaded: {len(all_events)}")
        print(f"🔍 DEBUG: Events after filtering: {len(filtered_events)}")
        print(f"🔍 DEBUG: Active events: {active_events}")
        print(f"🔍 DEBUG: Total liability: {total_liability}")
        print(f"🔍 DEBUG: Total revenue: {total_revenue}")
        
        conn.close()
        
        return jsonify({
            'events': paginated_events,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_events,
                'pages': (total_events + per_page - 1) // per_page
            },
            'summary': {
                'total_events': len(all_events),  # Show total available events, not filtered count
                'active_events': len([e for e in all_events if e.get('is_active', True)]),  # Count from all events
                'total_liability': total_liability,
                'total_revenue': total_revenue,
                'max_liability': total_liability,
                'max_possible_gain': total_revenue
            },
            'filters': {
                'sports': sorted(unique_sports),
                'markets': sorted(unique_markets)
            }
        })
        
    except Exception as e:
        print(f"Error in get_tenant_betting_events: {e}")
        return jsonify({'error': str(e)}), 500



@rich_admin_bp.route('/<subdomain>/admin/api/stats')
def get_tenant_stats(subdomain):
    """Get statistics for the tenant admin dashboard"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Get user count
        user_count = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE sportsbook_operator_id = ?", 
            (operator['id'],)
        ).fetchone()['count']
        
        # Get bet count
        bet_count = conn.execute("""
            SELECT COUNT(*) as count 
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            WHERE u.sportsbook_operator_id = ?
        """, (operator['id'],)).fetchone()['count']
        
        # Get total revenue (from won bets)
        revenue_result = conn.execute("""
            SELECT COALESCE(SUM(b.potential_return - b.stake), 0) as revenue
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            WHERE u.sportsbook_operator_id = ? AND b.status = 'won'
        """, (operator['id'],)).fetchone()
        total_revenue = float(revenue_result['revenue'] or 0)
        
        # Get active events count (events with pending bets)
        active_events_result = conn.execute("""
            SELECT COUNT(DISTINCT b.match_id) as count
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            WHERE u.sportsbook_operator_id = ? AND b.status = 'pending'
        """, (operator['id'],)).fetchone()
        active_events = active_events_result['count']
        
        conn.close()
        
        return jsonify({
            'total_users': user_count,
            'total_bets': bet_count,
            'total_revenue': total_revenue,
            'active_events': active_events
        })
        
    except Exception as e:
        print(f"Error getting tenant stats: {e}")
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/admin-check')
def admin_check(subdomain):
    """Check if admin is logged in and return operator info"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({
            'success': True,
            'logged_in': False,
            'operator': None
        })
    
    return jsonify({
        'success': True,
        'logged_in': True,
        'operator': {
            'id': operator['id'],
            'sportsbook_name': operator['sportsbook_name'],
            'subdomain': operator['subdomain'],
            'email': operator['email']
        }
    })

@rich_admin_bp.route('/<subdomain>/admin/api/users')
def get_tenant_users(subdomain):
    """Get users filtered by tenant"""
    print(f"🔍 DEBUG: get_tenant_users called for subdomain: {subdomain}")
    
    operator = get_operator_from_session()
    print(f"🔍 DEBUG: Operator from session: {operator}")
    
    if not operator:
        print("❌ DEBUG: No operator found in session")
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        print(f"🔍 DEBUG: Looking for users with sportsbook_operator_id = {operator['id']}")
        
        # Get users for this operator only
        users_query = """
        SELECT id, username, email, balance, created_at, is_active,
               (SELECT COUNT(*) FROM bets WHERE user_id = users.id) as total_bets,
               (SELECT COALESCE(SUM(stake), 0) FROM bets WHERE user_id = users.id) as total_staked,
               (SELECT COALESCE(SUM(potential_return), 0) FROM bets WHERE user_id = users.id AND status = 'won') as total_payout,
               (SELECT COALESCE(SUM(stake), 0) - COALESCE(SUM(potential_return), 0) FROM bets WHERE user_id = users.id AND status IN ('won', 'lost')) as profit
        FROM users 
        WHERE sportsbook_operator_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        users = conn.execute(users_query, (operator['id'], per_page, offset)).fetchall()
        print(f"🔍 DEBUG: Found {len(users)} users for operator {operator['id']}")
        
        # Get total count
        total_count = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE sportsbook_operator_id = ?", 
            (operator['id'],)
        ).fetchone()['count']
        
        print(f"🔍 DEBUG: Total user count: {total_count}")
        
        conn.close()
        
        return jsonify({
            'users': [dict(user) for user in users],
            'total': total_count,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        print(f"❌ DEBUG: Error in get_tenant_users: {e}")
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/user/<int:user_id>/toggle', methods=['POST'])
def toggle_user_status(subdomain, user_id):
    """Toggle user active status (tenant-filtered)"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Verify user belongs to this operator
        user = conn.execute(
            "SELECT id, is_active FROM users WHERE id = ? AND sportsbook_operator_id = ?",
            (user_id, operator['id'])
        ).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Toggle status
        new_status = not user['is_active']
        conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (new_status, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f"User {'enabled' if new_status else 'disabled'} successfully",
            'new_status': new_status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/betting-events/<event_key>/toggle', methods=['POST'])
def toggle_event_status(subdomain, event_key):
    """Toggle event active status (tenant-filtered)"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Check if event is currently disabled
        # The table structure is: event_key (auto-increment), sport (actual event_key), event_name, market
        disabled_event = conn.execute(
            'SELECT * FROM disabled_events WHERE sport = ?', 
            (event_key,)
        ).fetchone()
        
        if disabled_event:
            # Event is disabled, enable it by removing from disabled_events
            conn.execute('DELETE FROM disabled_events WHERE sport = ?', (event_key,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Event enabled successfully', 'status': 'enabled'})
        else:
            # Event is enabled, disable it by adding to disabled_events
            # Parse event_key to extract sport and market info
            try:
                # event_key format is "event_id_market_id" like "6220426_2"
                parts = event_key.split('_')
                if len(parts) >= 2:
                    event_id = parts[0]
                    market_id = parts[1]
                    # Get event details from the betting events to populate the table
                    event_details = conn.execute("""
                        SELECT sport_name, event_name, market 
                        FROM bets 
                        WHERE match_id = ? AND market = ? 
                        LIMIT 1
                    """, (event_id, market_id)).fetchone()
                    
                    if event_details:
                        sport_name = event_details['sport_name']
                        event_name = event_details['event_name'] or 'Unknown Event'
                        market = event_details['market'] or 'Unknown Market'
                    else:
                        sport_name = 'Unknown Sport'
                        event_name = 'Unknown Event'
                        market = 'Unknown Market'
                else:
                    sport_name = 'Unknown Sport'
                    event_name = 'Unknown Event'
                    market = 'Unknown Market'
                
                conn.execute(
                    'INSERT INTO disabled_events (sport, event_name, market) VALUES (?, ?, ?)',
                    (event_key, event_name, market)
                )
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': 'Event disabled successfully', 'status': 'disabled'})
            except Exception as parse_error:
                # Fallback if parsing fails
                conn.execute(
                    'INSERT INTO disabled_events (sport, event_name, market) VALUES (?, ?, ?)',
                    (event_key, 'Unknown Event', 'Unknown Market')
                )
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': 'Event disabled successfully', 'status': 'disabled'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/reports/overview')
def get_reports_overview(subdomain):
    """Get comprehensive reports overview (tenant-filtered)"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Total bets and revenue for this operator's users
        total_query = """
        SELECT 
            COUNT(*) as total_bets,
            SUM(b.stake) as total_stakes,
            SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as total_payouts,
            SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) as total_revenue_from_losses,
            COUNT(CASE WHEN b.status = 'pending' THEN 1 END) as pending_bets,
            COUNT(CASE WHEN b.status = 'won' THEN 1 END) as won_bets,
            COUNT(CASE WHEN b.status = 'lost' THEN 1 END) as lost_bets
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE u.sportsbook_operator_id = ?
        """
        
        totals = conn.execute(total_query, (operator['id'],)).fetchone()
        
        # Daily revenue for the last 30 days
        daily_query = """
        SELECT 
            DATE(b.created_at) as bet_date,
            COUNT(*) as daily_bets,
            SUM(b.stake) as daily_stakes,
            SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
            SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as daily_revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE u.sportsbook_operator_id = ? AND b.created_at >= date('now', '-30 days')
        GROUP BY DATE(b.created_at)
        ORDER BY bet_date DESC
        """
        
        daily_data = conn.execute(daily_query, (operator['id'],)).fetchall()
        
        # Sport-wise performance
        sport_query = """
        SELECT 
            b.sport_name,
            COUNT(*) as bets_count,
            SUM(b.stake) as total_stakes,
            SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
            SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as sport_revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE u.sportsbook_operator_id = ?
        GROUP BY b.sport_name
        ORDER BY sport_revenue DESC
        """
        
        sport_data = conn.execute(sport_query, (operator['id'],)).fetchall()
        
        conn.close()
        
        # Calculate metrics
        total_stakes = float(totals['total_stakes'] or 0)
        total_revenue_from_losses = float(totals['total_revenue_from_losses'] or 0)
        total_payouts = float(totals['total_payouts'] or 0)
        total_revenue = total_revenue_from_losses - total_payouts
        win_rate = (totals['won_bets'] / max(totals['total_bets'], 1)) * 100
        
        return jsonify({
            'overview': {
                'total_bets': totals['total_bets'] or 0,
                'total_stakes': total_stakes,
                'total_revenue': total_revenue,
                'win_rate': win_rate,
                'pending_bets': totals['pending_bets'] or 0,
                'won_bets': totals['won_bets'] or 0,
                'lost_bets': totals['lost_bets'] or 0
            },
            'daily_data': [dict(row) for row in daily_data],
            'sport_data': [dict(row) for row in sport_data]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/reports/generate', methods=['POST'])
def generate_custom_report(subdomain):
    """Generate custom reports based on parameters (tenant-filtered)"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        report_type = data.get('report_type', 'revenue')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        sport_filter = data.get('sport_filter')
        group_by = data.get('group_by', 'day')
        
        conn = get_db_connection()
        
        # Build base query with tenant filtering
        base_where = "u.sportsbook_operator_id = ?"
        params = [operator['id']]
        
        # Add date filters if provided
        if date_from:
            base_where += " AND DATE(b.created_at) >= ?"
            params.append(date_from)
        if date_to:
            base_where += " AND DATE(b.created_at) <= ?"
            params.append(date_to)
        if sport_filter:
            base_where += " AND b.sport_name = ?"
            params.append(sport_filter)
        
        # Generate report based on type
        if report_type == 'revenue':
            query = f"""
            SELECT 
                DATE(b.created_at) as bet_date,
                b.sport_name,
                COUNT(*) as total_bets,
                SUM(b.stake) as total_stakes,
                SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
                SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as revenue
            FROM bets b
            JOIN users u ON b.user_id = u.id
            WHERE {base_where}
            GROUP BY DATE(b.created_at), b.sport_name
            ORDER BY bet_date DESC, revenue DESC
            """
            
        elif report_type == 'user-activity':
            query = f"""
            SELECT 
                u.username,
                u.email,
                COUNT(b.id) as total_bets,
                SUM(b.stake) as total_staked,
                SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as payout,
                SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
                SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as user_profit,
                u.created_at as joined_date
            FROM users u
            LEFT JOIN bets b ON u.id = b.user_id
            WHERE u.sportsbook_operator_id = ?
            GROUP BY u.id, u.username, u.email, u.created_at
            ORDER BY total_bets DESC
            """
            params = [operator['id']]  # Reset params for user query
            
        elif report_type == 'betting-patterns':
            query = f"""
            SELECT 
                DATE(b.created_at) as bet_date,
                b.sport_name,
                b.market as bet_type,
                COUNT(*) as count,
                SUM(b.stake) as total_amount,
                (COUNT(CASE WHEN b.status = 'won' THEN 1 END) * 100.0 / COUNT(*)) as win_rate
            FROM bets b
            JOIN users u ON b.user_id = u.id
            WHERE {base_where}
            GROUP BY DATE(b.created_at), b.sport_name, b.market
            ORDER BY bet_date DESC, count DESC
            """
            
        elif report_type == 'sport-performance':
            query = f"""
            SELECT 
                b.sport_name,
                COUNT(*) as total_bets,
                SUM(b.stake) as total_stakes,
                COUNT(CASE WHEN b.status = 'won' THEN 1 END) as won_bets,
                COUNT(CASE WHEN b.status = 'lost' THEN 1 END) as lost_bets,
                SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
                SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as sport_revenue,
                (COUNT(CASE WHEN b.status = 'won' THEN 1 END) * 100.0 / COUNT(*)) as win_rate
            FROM bets b
            JOIN users u ON b.user_id = u.id
            WHERE {base_where}
            GROUP BY b.sport_name
            ORDER BY sport_revenue DESC
            """
        
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Execute query
        result = conn.execute(query, params).fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        report_data = [dict(row) for row in result]
        
        return jsonify(report_data)
        
    except Exception as e:
        print(f"Error generating custom report: {e}")
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/reports/available-sports')
def get_available_sports_for_reports(subdomain):
    """Get available sports for report filtering (tenant-filtered)"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Get sports that have bets from this operator's users
        sports_query = """
        SELECT DISTINCT b.sport_name
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE u.sportsbook_operator_id = ?
        ORDER BY b.sport_name
        """
        
        sports_result = conn.execute(sports_query, (operator['id'],)).fetchall()
        conn.close()
        
        sports = [row['sport_name'] for row in sports_result]
        
        return jsonify({'sports': sports})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/reports/export', methods=['POST'])
def export_custom_report(subdomain):
    """Export custom report to CSV (tenant-filtered)"""
    operator = get_operator_from_session()
    if not operator:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        report_type = data.get('report_type', 'revenue')
        format_type = data.get('format', 'csv')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        sport_filter = data.get('sport_filter')
        
        print(f"DEBUG: Export request - type: {report_type}, format: {format_type}, from: {date_from}, to: {date_to}, sport: {sport_filter}")
        
        # For now, just return a simple CSV response
        # In a production system, you might want to use a proper CSV library
        conn = get_db_connection()
        
        # Build base query (similar to generate endpoint)
        base_where = "u.sportsbook_operator_id = ?"
        params = [operator['id']]
        
        if date_from:
            base_where += " AND DATE(b.created_at) >= ?"
            params.append(date_from)
        if date_to:
            base_where += " AND DATE(b.created_at) <= ?"
            params.append(date_to)
        if sport_filter:
            base_where += " AND b.sport_name = ?"
            params.append(sport_filter)
        
        # Generate CSV data
        if report_type == 'revenue':
            query = f"""
            SELECT 
                DATE(b.created_at) as bet_date,
                b.sport_name,
                COUNT(*) as total_bets,
                SUM(b.stake) as total_stakes,
                SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
                SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as revenue
            FROM bets b
            JOIN users u ON b.user_id = u.id
            WHERE {base_where}
            GROUP BY DATE(b.created_at), b.sport_name
            ORDER BY bet_date DESC, revenue DESC
            """
            headers = ['Date', 'Sport', 'Total Bets', 'Total Stakes', 'Revenue']
        
        elif report_type == 'user-activity':
            query = f"""
            SELECT 
                u.username,
                u.email,
                COUNT(b.id) as total_bets,
                SUM(b.stake) as total_staked,
                SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as payout,
                SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
                SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as user_profit,
                u.created_at as joined_date
            FROM users u
            LEFT JOIN bets b ON u.id = b.user_id
            WHERE u.sportsbook_operator_id = ?
            GROUP BY u.id, u.username, u.email, u.created_at
            ORDER BY total_bets DESC
            """
            headers = ['Username', 'Email', 'Total Bets', 'Total Staked', 'Payout', 'Profit', 'Join Date']
            params = [operator['id']]
        
        else:
            return jsonify({'error': 'Export not supported for this report type'}), 400
        
        # Execute query
        try:
            result = conn.execute(query, params).fetchall()
            print(f"DEBUG: Query executed successfully, got {len(result)} rows")
        except Exception as query_error:
            print(f"DEBUG: Query execution error: {query_error}")
            print(f"DEBUG: Query: {query}")
            print(f"DEBUG: Params: {params}")
            conn.close()
            raise query_error
        
        conn.close()
        
        # Generate CSV content
        csv_content = ','.join(headers) + '\n'
        for row in result:
            csv_row = []
            for i, value in enumerate(row):
                # Escape commas and quotes in CSV
                if ',' in str(value) or '"' in str(value):
                    value = f'"{str(value).replace(chr(34), chr(34) + chr(34))}"'
                csv_row.append(str(value))
            csv_content += ','.join(csv_row) + '\n'
        
        # Return CSV file
        from flask import Response
        response = Response(csv_content, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
        return response
        
    except Exception as e:
        print(f"Error exporting report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@rich_admin_bp.route('/<subdomain>/admin/api/session-test')
def session_test(subdomain):
    """Test endpoint to debug session issues"""
    print(f"🔍 DEBUG: Session test called for subdomain: {subdomain}")
    print(f"🔍 DEBUG: Full session data: {dict(session)}")
    print(f"🔍 DEBUG: admin_id: {session.get('admin_id')}")
    print(f"🔍 DEBUG: admin_subdomain: {session.get('admin_subdomain')}")
    print(f"🔍 DEBUG: admin_username: {session.get('admin_username')}")
    
    return jsonify({
        'session_data': dict(session),
        'admin_id': session.get('admin_id'),
        'admin_subdomain': session.get('admin_subdomain'),
        'admin_username': session.get('admin_username')
    })

# Rich Admin Template (extracted from original admin_app.py)
RICH_ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ operator.sportsbook_name }} - Admin Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header h1 {
            font-size: 1.5rem;
        }
        
        .header .admin-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logout-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .nav-tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        
        .nav-tab {
            padding: 0.75rem 1.5rem;
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .nav-tab.active {
            background: #4CAF50;
            color: white;
        }
        
        .nav-tab:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .content-section {
            display: none;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .content-section.active {
            display: block;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
        }
        
        .summary-card h3 {
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            opacity: 0.9;
        }
        
        .summary-card .value {
            font-size: 1.8rem;
            font-weight: bold;
        }
        
        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .controls select, .controls input, .controls button {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .controls button {
            background: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        
        .controls button:hover {
            background: #45a049;
        }
        
        .table-container {
            overflow-x: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }
        
        th:hover {
            background: #e9ecef;
        }
        
        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-active {
            background: #d4edda;
            color: #155724;
        }
        
        .status-disabled {
            background: #f8d7da;
            color: #721c24;
        }
        
        .action-btn {
            padding: 0.25rem 0.75rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .btn-enable {
            background: #28a745;
            color: white;
        }
        
        .btn-disable {
            background: #dc3545;
            color: white;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        
        /* Report Builder Styles */
        .report-builder-form {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid #e9ecef;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .form-group.full-width {
            grid-column: 1 / -1;
        }
        
        .form-group label {
            font-weight: 600;
            color: #495057;
            font-size: 0.9rem;
        }
        
        .form-group select,
        .form-group input {
            padding: 0.75rem;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: 0.9rem;
            background: white;
            transition: border-color 0.2s ease;
        }
        
        .form-group select:focus,
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .date-inputs {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .date-inputs input {
            flex: 1;
        }
        
        .generate-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .form-section {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #e9ecef;
        }
        
        .form-section h3 {
            color: #495057;
            margin-bottom: 1.5rem;
            font-size: 1.2rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.75rem;
        }
        
        .form-section h2 {
            color: #2c3e50;
            margin-bottom: 2rem;
            font-size: 1.8rem;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .form-help-text {
            font-size: 0.85rem;
            color: #6c757d;
            margin-top: 0.25rem;
            font-style: italic;
        }
        
        .form-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #dee2e6, transparent);
            margin: 2rem 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 {{ operator.sportsbook_name }} - Admin Dashboard</h1>
        <div class="admin-info">
            <span>Welcome, {{ operator.login }}</span>
            <a href="/{{ operator.subdomain }}/admin/logout" class="logout-btn">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showSection('betting-events')">📊 Betting Events</button>
            <button class="nav-tab" onclick="showSection('user-management')">👥 User Management</button>
            <button class="nav-tab" onclick="showSection('reports')">📈 Reports</button>
            <button class="nav-tab" onclick="showSection('report-builder')">🔧 Report Builder</button>
            <button class="nav-tab" onclick="openThemeCustomizer()">🎨 Theme Customizer</button>
        </div>
        
        <!-- Betting Events Section -->
        <div id="betting-events" class="content-section active">
            <h2>Betting Events Management</h2>
            <div class="summary-cards">
                <div class="summary-card">
                    <h3>Total Events</h3>
                    <div class="value" id="total-events">0</div>
                </div>
                <div class="summary-card">
                    <h3>Active Events</h3>
                    <div class="value" id="active-events">0</div>
                </div>
                <div class="summary-card">
                    <h3>Max Liability</h3>
                    <div class="value" id="max-liability">$0.00</div>
                </div>
                <div class="summary-card">
                    <h3>Max Possible Gain</h3>
                    <div class="value" id="max-gain">$0.00</div>
                </div>
            </div>
            
            <div class="controls">
                <select id="sport-filter">
                    <option value="">All Sports</option>
                </select>
                <select id="market-filter">
                    <option value="">All Markets</option>
                </select>
                <input type="text" id="search-events" placeholder="Search events...">
                <label style="margin-left: 10px; display: flex; align-items: center; gap: 5px; font-size: 14px; color: #666;">
                    <input type="checkbox" id="show-only-with-bets" checked style="margin: 0;">
                    Show Only Events with Bets (Faster)
                </label>
                <button onclick="loadBettingEvents()">🔄 Refresh Events</button>
            </div>
            
            <div class="table-container">
                <table id="events-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable('events-table', 0)" style="cursor: pointer;">
                                Event ID <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('events-table', 1)" style="cursor: pointer;">
                                Sport <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('events-table', 2)" style="cursor: pointer;">
                                Event Name <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('events-table', 3)" style="cursor: pointer;">
                                Market <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('events-table', 4)" style="cursor: pointer;">
                                Total Bets <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('events-table', 5)" style="cursor: pointer;">
                                Liability <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('events-table', 6)" style="cursor: pointer;">
                                Revenue <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('events-table', 7)" style="cursor: pointer;">
                                Status <span class="sort-icon">↕</span>
                            </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="events-tbody">
                        <tr><td colspan="9" class="loading">Loading events...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- User Management Section -->
        <div id="user-management" class="content-section">
            <h2>User Management</h2>
            <p>Manage users across your sportsbook operations</p>
            
            <div class="controls">
                <button onclick="loadUsers()">🔄 Refresh Users</button>
            </div>
            
            <div class="table-container">
                <table id="users-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable('users-table', 0)" style="cursor: pointer;">
                                ID <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 1)" style="cursor: pointer;">
                                Username <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 2)" style="cursor: pointer;">
                                Email <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 3)" style="cursor: pointer;">
                                Balance <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 4)" style="cursor: pointer;">
                                Bets <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 5)" style="cursor: pointer;">
                                Staked <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 6)" style="cursor: pointer;">
                                Payout <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 7)" style="cursor: pointer;">
                                Profit <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 8)" style="cursor: pointer;">
                                Joined <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('users-table', 9)" style="cursor: pointer;">
                                Status <span class="sort-icon">↕</span>
                            </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="users-tbody">
                        <tr><td colspan="11" class="loading">Loading users...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Reports Section -->
        <div id="reports" class="content-section">
            <h2>Reports & Analytics</h2>
            <div class="summary-cards">
                <div class="summary-card">
                    <h3>Total Revenue</h3>
                    <div class="value" id="total-revenue">$0.00</div>
                </div>
                <div class="summary-card">
                    <h3>Total Bets</h3>
                    <div class="value" id="total-bets-count">0</div>
                </div>
                <div class="summary-card">
                    <h3>Active Users</h3>
                    <div class="value" id="active-users-count">0</div>
                </div>
                <div class="summary-card">
                    <h3>Profit Margin</h3>
                    <div class="value" id="profit-margin">0%</div>
                </div>
            </div>
            
            <div class="controls">
                <select id="report-period">
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month" selected>This Month</option>
                    <option value="year">This Year</option>
                </select>
                <button onclick="loadReports()">🔄 Refresh Reports</button>
                <button onclick="exportReport()">📊 Export CSV</button>
            </div>
            
            <div class="report-charts">
                <div class="chart-container">
                    <h3>Revenue by Sport</h3>
                    <canvas id="revenue-by-sport-chart" width="400" height="200"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Betting Activity</h3>
                    <canvas id="betting-activity-chart" width="400" height="200"></canvas>
                </div>
            </div>
            
            <div class="table-container">
                <h3>Detailed Reports</h3>
                <table id="reports-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable('reports-table', 0)" style="cursor: pointer;">
                                Date <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('reports-table', 1)" style="cursor: pointer;">
                                Sport <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('reports-table', 2)" style="cursor: pointer;">
                                Total Bets <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('reports-table', 3)" style="cursor: pointer;">
                                Total Stakes <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('reports-table', 4)" style="cursor: pointer;">
                                Total Payouts <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('reports-table', 5)" style="cursor: pointer;">
                                Revenue <span class="sort-icon">↕</span>
                            </th>
                            <th onclick="sortTable('reports-table', 6)" style="cursor: pointer;">
                                Profit Margin <span class="sort-icon">↕</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody id="reports-tbody">
                        <tr><td colspan="7" class="loading">Loading reports...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Report Builder Section -->
        <div id="report-builder" class="content-section">
            <h2>Custom Report Builder</h2>
            
            <div class="form-section">
                <h3>📊 Report Configuration</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>Report Type:</label>
                        <select id="report-type">
                            <option value="revenue">Revenue Analysis</option>
                            <option value="user-activity">User Activity</option>
                            <option value="betting-patterns">Betting Patterns</option>
                            <option value="sport-performance">Sport Performance</option>
                        </select>
                        <div class="form-help-text">Choose the type of analysis you want to generate</div>
                    </div>
                    <div class="form-group">
                        <label>Group By:</label>
                        <select id="group-by">
                            <option value="day">Day</option>
                            <option value="week">Week</option>
                            <option value="month">Month</option>
                            <option value="sport">Sport</option>
                            <option value="user">User</option>
                        </select>
                        <div class="form-help-text">Select how to group the data in your report</div>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Sport Filter:</label>
                        <select id="sport-filter-report">
                            <option value="">All Sports</option>
                        </select>
                        <div class="form-help-text">Filter results by specific sports (optional)</div>
                    </div>
                    <div class="form-group">
                        <label>Date Range:</label>
                        <div class="date-inputs">
                            <input type="date" id="start-date" placeholder="Start Date">
                            <input type="date" id="end-date" placeholder="End Date">
                        </div>
                        <div class="form-help-text">Select the time period for your report</div>
                    </div>
                </div>
                
                <div class="form-divider"></div>
                
                <button class="generate-btn" onclick="generateCustomReport()">
                    📊 Generate Report
                </button>
            </div>
            
            <div id="custom-report-results" class="form-section" style="display: none;">
                <h3>📈 Custom Report Results</h3>
                <div class="table-container">
                    <table id="custom-report-table">
                        <thead id="custom-report-thead"></thead>
                        <tbody id="custom-report-tbody"></tbody>
                    </table>
                </div>
                <button class="generate-btn" onclick="exportCustomReport()" style="margin-top: 1rem;">
                    📊 Export Custom Report
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const SUBDOMAIN = '{{ operator.subdomain }}';
        
        function updateFilterOptions(filters) {
            // Update sport filter
            const sportSelect = document.getElementById('sport-filter');
            const currentSport = sportSelect.value;
            sportSelect.innerHTML = '<option value="">All Sports</option>';
            if (filters?.sports) {
                filters.sports.forEach(sport => {
                    const option = document.createElement('option');
                    option.value = sport;
                    option.textContent = sport;
                    if (sport === currentSport) option.selected = true;
                    sportSelect.appendChild(option);
                });
            }
            
            // Update market filter
            const marketSelect = document.getElementById('market-filter');
            const currentMarket = marketSelect.value;
            marketSelect.innerHTML = '<option value="">All Markets</option>';
            if (filters?.markets) {
                filters.markets.forEach(market => {
                    const option = document.createElement('option');
                    option.value = market;
                    option.textContent = market;
                    if (market === currentMarket) option.selected = true;
                    marketSelect.appendChild(option);
                });
            }
        }
        

        
        async function loadBettingEvents() {
            try {
                // Get all filter values
                const showOnlyWithBets = document.getElementById('show-only-with-bets').checked;
                const sportFilter = document.getElementById('sport-filter').value;
                const marketFilter = document.getElementById('market-filter').value;
                const searchQuery = document.getElementById('search-events').value;
                
                // Build query string
                const params = new URLSearchParams();
                params.append('show_only_with_bets', showOnlyWithBets);
                if (sportFilter) params.append('sport', sportFilter);
                if (marketFilter) params.append('market', marketFilter);
                if (searchQuery) params.append('search', searchQuery);
                
                const response = await fetch(`/${SUBDOMAIN}/admin/api/betting-events?${params.toString()}`);
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('events-tbody').innerHTML = 
                        `<tr><td colspan="8" class="error">Error: ${data.error}</td></tr>`;
                    return;
                }
                
                // Update summary cards with correct data
                document.getElementById('total-events').textContent = data.summary?.total_events || 0;
                document.getElementById('active-events').textContent = data.summary?.active_events || 0;
                document.getElementById('max-liability').textContent = `$${(data.summary?.total_liability || 0).toFixed(2)}`;
                document.getElementById('max-gain').textContent = `$${(data.summary?.total_revenue || 0).toFixed(2)}`;
                
                // Update filter options
                updateFilterOptions(data.filters);
                
                // Update table
                const tbody = document.getElementById('events-tbody');
                if (data.events.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" class="loading">No events found</td></tr>';
                } else {
                    tbody.innerHTML = data.events.map(event => `
                        <tr>
                            <td data-sort="${event.id}">${event.id}</td>
                            <td data-sort="${event.sport}">${event.sport}</td>
                            <td data-sort="${event.name}">${event.name}</td>
                            <td data-sort="${event.market}">${event.market}</td>
                            <td data-sort="${event.total_bets || 0}">${event.total_bets || 0}</td>
                            <td data-sort="${event.liability || 0}" class="liability">$${event.liability || '0.00'}</td>
                            <td data-sort="${event.revenue || 0}" class="revenue">$${event.revenue || '0.00'}</td>
                            <td data-sort="${event.status}"><span class="status-badge status-${event.status}">${event.status}</span></td>
                            <td>
                                <button class="action-btn btn-disable" onclick="toggleEvent('${event.id}')">
                                    ${event.is_disabled ? 'Enable' : 'Disable'}
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
                
            } catch (error) {
                document.getElementById('events-tbody').innerHTML = 
                    `<tr><td colspan="9" class="error">Error loading events: ${error.message}</td></tr>`;
            }
        }
        
        async function toggleEvent(eventId) {
            try {
                const response = await fetch(`/${SUBDOMAIN}/admin/api/betting-events/${eventId}/toggle`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    loadBettingEvents(); // Reload the events table
                } else {
                    alert('Error: ' + data.error);
                }
                
            } catch (error) {
                alert('Error toggling event status: ' + error.message);
            }
        }
        
        async function loadReports() {
            try {
                const response = await fetch(`/${SUBDOMAIN}/admin/api/reports/overview`);
                const data = await response.json();
                
                if (data.error) {
                    console.error('Error loading reports:', data.error);
                    return;
                }
                
                // Update summary cards
                document.getElementById('total-revenue').textContent = `$${data.overview.total_revenue.toFixed(2)}`;
                document.getElementById('total-bets-count').textContent = data.overview.total_bets;
                document.getElementById('active-users-count').textContent = data.overview.pending_bets;
                document.getElementById('profit-margin').textContent = `${data.overview.win_rate.toFixed(1)}%`;
                
                // Update reports table
                const tbody = document.getElementById('reports-tbody');
                if (data.sport_data && data.sport_data.length > 0) {
                    tbody.innerHTML = data.sport_data.map(sport => `
                        <tr>
                            <td data-sort="${new Date().getTime()}">${new Date().toLocaleDateString()}</td>
                            <td data-sort="${sport.sport_name}">${sport.sport_name}</td>
                            <td data-sort="${sport.bets_count}">${sport.bets_count}</td>
                            <td data-sort="${sport.total_stakes}">$${sport.total_stakes.toFixed(2)}</td>
                            <td data-sort="${sport.total_stakes - sport.sport_revenue}">$${(sport.total_stakes - sport.sport_revenue).toFixed(2)}</td>
                            <td data-sort="${sport.sport_revenue}">$${sport.sport_revenue.toFixed(2)}</td>
                            <td data-sort="${(sport.sport_revenue / Math.max(sport.total_stakes, 1)) * 100}">${((sport.sport_revenue / Math.max(sport.total_stakes, 1)) * 100).toFixed(1)}%</td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="7" class="loading">No report data available</td></tr>';
                }
                
            } catch (error) {
                console.error('Error loading reports:', error);
                document.getElementById('reports-tbody').innerHTML = 
                    `<tr><td colspan="7" class="error">Error loading reports: ${error.message}</td></tr>`;
            }
        }
        
        async function loadUsers() {
            try {
                const response = await fetch(`/${SUBDOMAIN}/admin/api/users`);
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('users-tbody').innerHTML = 
                        `<tr><td colspan="11" class="error">Error: ${data.error}</td></tr>`;
                    return;
                }
                
                const tbody = document.getElementById('users-tbody');
                if (data.users.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="11" class="loading">No users found</td></tr>';
                } else {
                    tbody.innerHTML = data.users.map(user => `
                        <tr>
                            <td data-sort="${user.id}">${user.id}</td>
                            <td data-sort="${user.username}">${user.username}</td>
                            <td data-sort="${user.email}">${user.email}</td>
                            <td data-sort="${user.balance}">$${user.balance}</td>
                            <td data-sort="${user.total_bets}">${user.total_bets}</td>
                            <td data-sort="${user.total_staked}">$${user.total_staked}</td>
                            <td data-sort="${user.total_payout}">$${user.total_payout}</td>
                            <td data-sort="${user.profit}">$${user.profit}</td>
                            <td data-sort="${new Date(user.created_at).getTime()}">${new Date(user.created_at).toLocaleDateString()}</td>
                            <td data-sort="${user.is_active ? 'active' : 'disabled'}"><span class="status-badge status-${user.is_active ? 'active' : 'disabled'}">${user.is_active ? 'Active' : 'Disabled'}</span></td>
                            <td>
                                <button class="action-btn ${user.is_active ? 'btn-disable' : 'btn-enable'}" 
                                        onclick="toggleUserStatus(${user.id})">
                                    ${user.is_active ? 'Disable' : 'Enable'}
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
                
            } catch (error) {
                document.getElementById('users-tbody').innerHTML = 
                    `<tr><td colspan="11" class="error">Error loading users: ${error.message}</td></tr>`;
            }
        }
        
        async function toggleUserStatus(userId) {
            try {
                const response = await fetch(`/${SUBDOMAIN}/admin/api/user/${userId}/toggle`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    loadUsers(); // Reload the users table
                } else {
                    alert('Error: ' + data.error);
                }
                
            } catch (error) {
                alert('Error toggling user status: ' + error.message);
            }
        }
        
        function openThemeCustomizer() {
            // Open theme customizer in new tab for this specific operator
            window.open(`/${SUBDOMAIN}/admin/theme-customizer`, '_blank');
        }

        // Table sorting function
        function sortTable(tableId, columnIndex) {
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Get current sort direction
            const header = table.querySelector(`th:nth-child(${columnIndex + 1})`);
            const currentDirection = header.getAttribute('data-sort-direction') || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            
            // Update all headers to remove sort indicators
            table.querySelectorAll('th').forEach(th => {
                th.setAttribute('data-sort-direction', '');
                const icon = th.querySelector('.sort-icon');
                if (icon) icon.textContent = '↕';
            });
            
            // Update current header
            header.setAttribute('data-sort-direction', newDirection);
            const icon = header.querySelector('.sort-icon');
            if (icon) icon.textContent = newDirection === 'asc' ? '↑' : '↓';
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.cells[columnIndex].getAttribute('data-sort') || a.cells[columnIndex].textContent;
                const bValue = b.cells[columnIndex].getAttribute('data-sort') || b.cells[columnIndex].textContent;
                
                // Handle numeric values
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
                }
                
                // Handle string values
                const aStr = String(aValue).toLowerCase();
                const bStr = String(bValue).toLowerCase();
                
                if (newDirection === 'asc') {
                    return aStr.localeCompare(bStr);
                } else {
                    return bStr.localeCompare(aStr);
                }
            });
            
            // Reorder rows in the table
            rows.forEach(row => tbody.appendChild(row));
        }
        
        async function loadReportBuilder() {
            try {
                // Load available sports for report filtering
                const response = await fetch(`/${SUBDOMAIN}/admin/api/reports/available-sports`);
                const data = await response.json();
                
                const sportFilter = document.getElementById('sport-filter-report');
                sportFilter.innerHTML = '<option value="">All Sports</option>';
                
                if (data.sports) {
                    data.sports.forEach(sport => {
                        const option = document.createElement('option');
                        option.value = sport;
                        option.textContent = sport;
                        sportFilter.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('Error loading sports for report builder:', error);
            }
        }
        
        async function generateCustomReport() {
            try {
                const reportType = document.getElementById('report-type').value;
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;
                const sportFilter = document.getElementById('sport-filter-report').value;
                const groupBy = document.getElementById('group-by').value;
                
                // Show loading state
                const resultsDiv = document.getElementById('custom-report-results');
                resultsDiv.style.display = 'block';
                
                const tbody = document.getElementById('custom-report-tbody');
                const thead = document.getElementById('custom-report-thead');
                
                tbody.innerHTML = '<tr><td colspan="5" class="loading">Generating report...</td></tr>';
                
                // Generate report data
                const response = await fetch(`/${SUBDOMAIN}/admin/api/reports/generate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        report_type: reportType,
                        date_from: startDate || null,
                        date_to: endDate || null,
                        sport_filter: sportFilter || null,
                        group_by: groupBy
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    tbody.innerHTML = `<tr><td colspan="5" class="error">Error: ${data.error}</td></tr>`;
                    return;
                }
                
                // Update table headers based on report type
                const headers = getReportHeaders(reportType, groupBy);
                thead.innerHTML = `<tr>${headers.map((h, index) => `<th onclick="sortTable('custom-report-table', ${index})" style="cursor: pointer;">${h} <span class="sort-icon">↕</span></th>`).join('')}</tr>`;
                
                // Update table body with report data
                if (data.length > 0) {
                    tbody.innerHTML = data.map(row => {
                        const cells = getReportCells(row, reportType, groupBy);
                        const sortValues = getReportSortValues(row, reportType, groupBy);
                        return `<tr>${cells.map((cell, index) => `<td data-sort="${sortValues[index]}">${cell}</td>`).join('')}</tr>`;
                    }).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="' + headers.length + '" class="loading">No data found for the selected criteria</td></tr>';
                }
                
            } catch (error) {
                console.error('Error generating custom report:', error);
                const tbody = document.getElementById('custom-report-tbody');
                tbody.innerHTML = `<tr><td colspan="5" class="error">Error generating report: ${error.message}</td></tr>`;
            }
        }
        
        function getReportHeaders(reportType, groupBy) {
            const headerMap = {
                'revenue': ['Date', 'Sport', 'Total Bets', 'Total Stakes', 'Revenue', 'Profit Margin'],
                'user-activity': ['Username', 'Email', 'Total Bets', 'Total Staked', 'Payout', 'Profit', 'Join Date'],
                'betting-patterns': ['Date', 'Sport', 'Bet Type', 'Count', 'Total Amount', 'Win Rate'],
                'sport-performance': ['Sport', 'Total Bets', 'Total Stakes', 'Won Bets', 'Lost Bets', 'Revenue', 'Win Rate']
            };
            
            return headerMap[reportType] || ['Data', 'Value'];
        }
        
        function getReportCells(row, reportType, groupBy) {
            switch (reportType) {
                case 'revenue':
                    return [
                        row.bet_date || row.report_date || 'N/A',
                        row.sport_name || 'N/A',
                        row.total_bets || 0,
                        `$${(row.total_stakes || 0).toFixed(2)}`,
                        `$${(row.revenue || 0).toFixed(2)}`,
                        `${((row.revenue || 0) / Math.max(row.total_stakes || 1, 1) * 100).toFixed(1)}%`
                    ];
                case 'user-activity':
                    return [
                        row.username || 'N/A',
                        row.email || 'N/A',
                        row.total_bets || 0,
                        `$${(row.total_staked || 0).toFixed(2)}`,
                        `$${(row.payout || 0).toFixed(2)}`,
                        `$${(row.user_profit || 0).toFixed(2)}`,
                        new Date(row.joined_date || Date.now()).toLocaleDateString()
                    ];
                case 'betting-patterns':
                    return [
                        row.bet_date || 'N/A',
                        row.sport_name || 'N/A',
                        row.bet_type || 'N/A',
                        row.count || 0,
                        `$${(row.total_amount || 0).toFixed(2)}`,
                        `${(row.win_rate || 0).toFixed(1)}%`
                    ];
                case 'sport-performance':
                    return [
                        row.sport_name || 'N/A',
                        row.total_bets || 0,
                        `$${(row.total_stakes || 0).toFixed(2)}`,
                        row.won_bets || 0,
                        row.lost_bets || 0,
                        `$${(row.sport_revenue || 0).toFixed(2)}`,
                        `${(row.win_rate || 0).toFixed(1)}%`
                    ];
                default:
                    return Object.values(row);
            }
        }

        function getReportSortValues(row, reportType, groupBy) {
            switch (reportType) {
                case 'revenue':
                    return [
                        new Date(row.bet_date || row.report_date || Date.now()).getTime(),
                        row.sport_name || '',
                        row.total_bets || 0,
                        row.total_stakes || 0,
                        row.revenue || 0,
                        (row.revenue || 0) / Math.max(row.total_stakes || 1, 1) * 100
                    ];
                case 'user-activity':
                    return [
                        row.username || '',
                        row.email || '',
                        row.total_bets || 0,
                        row.total_staked || 0,
                        row.payout || 0,
                        row.user_profit || 0,
                        new Date(row.joined_date || Date.now()).getTime()
                    ];
                case 'betting-patterns':
                    return [
                        new Date(row.bet_date || Date.now()).getTime(),
                        row.sport_name || '',
                        row.bet_type || '',
                        row.count || 0,
                        row.total_amount || 0,
                        row.win_rate || 0
                    ];
                case 'sport-performance':
                    return [
                        row.sport_name || '',
                        row.total_bets || 0,
                        row.total_stakes || 0,
                        row.won_bets || 0,
                        row.lost_bets || 0,
                        row.sport_revenue || 0,
                        row.win_rate || 0
                    ];
                default:
                    return Object.values(row);
            }
        }
        
        async function exportCustomReport() {
            try {
                const reportType = document.getElementById('report-type').value;
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;
                const sportFilter = document.getElementById('sport-filter-report').value;
                const format = 'csv'; // Default to CSV for now
                
                const response = await fetch(`/${SUBDOMAIN}/admin/api/reports/export`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        report_type: reportType,
                        format: format,
                        date_from: startDate || null,
                        date_to: endDate || null,
                        sport_filter: sportFilter || null
                    })
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    
                    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                    a.download = `${reportType}_${timestamp}.${format}`;
                    
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    throw new Error('Failed to export report');
                }
                
            } catch (error) {
                console.error('Error exporting custom report:', error);
                alert('Failed to export report. Please try again.');
            }
        }
        
        function showSection(sectionId) {
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected section
            document.getElementById(sectionId).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Load data for specific sections
            if (sectionId === 'betting-events') {
                loadBettingEvents();
            } else if (sectionId === 'reports') {
                loadReports();
            } else if (sectionId === 'user-management') {
                loadUsers();
            }
        }
        
        // Load initial data
        document.addEventListener('DOMContentLoaded', function() {
            loadBettingEvents();
            
            // Add event listeners for filters and search
            document.getElementById('sport-filter').addEventListener('change', () => loadBettingEvents());
            document.getElementById('market-filter').addEventListener('change', () => loadBettingEvents());
            document.getElementById('search-events').addEventListener('input', () => loadBettingEvents());
            
            // Add event listener for the checkbox
            document.getElementById('show-only-with-bets').addEventListener('change', () => loadBettingEvents());
        });
    </script>
</body>
</html>
'''

