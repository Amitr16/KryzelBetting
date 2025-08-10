"""
Rich Super Admin Interface - Based on original admin_app.py but with global scope
Same rich interface as admin_app.py but shows data across all operators
"""

from flask import Blueprint, request, session, redirect, render_template_string, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
import os

rich_superadmin_bp = Blueprint('rich_superadmin', __name__)

DATABASE_PATH = 'src/database/app.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_global_event_financials(event_id, market_id, sport_name):
    """Calculate max liability and max possible gain for a specific event+market combination across ALL operators"""
    try:
        conn = get_db_connection()
        
        # Get all pending bets for this specific event+market combination from ALL operators
        query = """
        SELECT b.bet_selection, b.stake, b.potential_return, b.odds
        FROM bets b
        JOIN users u ON b.user_id = u.id
        JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
        WHERE b.match_id = ? AND b.market = ? AND b.sport_name = ? AND b.status = 'pending'
        AND op.is_active = 1
        """
        
        bets = conn.execute(query, (event_id, market_id, sport_name)).fetchall()
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
        print(f"Error calculating global financials: {e}")
        return 0.0, 0.0

def check_superadmin_auth(f):
    """Decorator to check if user is authenticated as super admin"""
    def decorated_function(*args, **kwargs):
        if not ('superadmin_id' in session):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@rich_superadmin_bp.route('/superadmin/rich-dashboard')
@check_superadmin_auth
def rich_superadmin_dashboard():
    """Rich super admin dashboard with same interface as original admin_app.py"""
    return render_template_string(RICH_SUPERADMIN_TEMPLATE)

@rich_superadmin_bp.route('/superadmin/api/global-betting-events', methods=['POST'])
@check_superadmin_auth
def get_global_betting_events():
    """Get global betting events across all operators with global liability calculations"""
    try:
        data = request.get_json()
        sport_filter = data.get('sport', '')
        market_filter = data.get('market', '')
        search_term = data.get('search', '')
        show_bets_only = data.get('show_bets_only', True)

        conn = get_db_connection()
        
        # First, query the database to find which event_market combinations have bets across all operators
        if show_bets_only:
            # Get events with bets from database first
            bet_events_query = """
                SELECT DISTINCT b.match_id, b.sport_name, b.market, COUNT(*) as bet_count
        FROM bets b
                JOIN users u ON b.user_id = u.id 
                JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
                WHERE op.is_active = 1
                GROUP BY b.match_id, b.sport_name, b.market
                HAVING COUNT(*) > 0
                ORDER BY bet_count DESC
            """
            bet_events_result = conn.execute(bet_events_query).fetchall()
            
            # Create a set of events to load
            events_to_load = set()
            for row in bet_events_result:
                match_id = str(row['match_id'])
                sport_name = str(row['sport_name'])
                market_id = str(row['market'])
                events_to_load.add((match_id, sport_name, market_id))
        
        # Load sports and events data directly from JSON files
        import os
        import json
        
        # Path to Sports Pre Match directory
        sports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Sports Pre Match')
        
        if not os.path.exists(sports_dir):
            return jsonify({'error': 'Sports directory not found'})
        
        all_events = []
        all_sports = set()
        all_markets = set()
        
        # Load sports data
        sport_folders = [f for f in os.listdir(sports_dir) if os.path.isdir(os.path.join(sports_dir, f))]
        
        for sport_folder in sport_folders:
            sport_path = os.path.join(sports_dir, sport_folder)
            sport_display_name = sport_folder.title()
            
            # Apply sport filter if specified
            if sport_filter and sport_display_name.lower() != sport_filter.lower():
                continue
            
            # Load events for this sport
            events_file = os.path.join(sport_path, f'{sport_folder}_odds.json')
            
            if os.path.exists(events_file):
                try:
                    with open(events_file, 'r', encoding='utf-8') as f:
                        sport_data = json.load(f)
                    
                    # Extract events from the JSON structure
                    sport_events = []
                    if 'odds_data' in sport_data and 'scores' in sport_data['odds_data'] and 'categories' in sport_data['odds_data']['scores']:
                        for category in sport_data['odds_data']['scores']['categories']:
                            if 'matches' in category:
                                # Add category info to each match
                                for match in category['matches']:
                                    match['_category_name'] = category.get('name', 'Unknown Category')
                                sport_events.extend(category['matches'])
                    
                    # Process each event
                    for event in sport_events:
                        event_id = event.get('id', '')
                        
                        # Process markets/odds
                        if 'odds' in event:
                            for odd in event['odds']:
                                market_name = odd.get('value', '').lower()
                                market_id = odd.get('id', '')
                                
                                if not market_id:
                                    continue
                                
                                # If we're only showing events with bets, check if this event_market has bets
                                if show_bets_only:
                                    event_key = (str(event_id), str(sport_folder), str(market_id))
                                    if event_key not in events_to_load:
                                        continue  # Skip this event_market combination
                                
                                # Apply market filter if specified
                                if market_filter and market_name.lower() != market_filter.lower():
                                    continue
                                
                                # Apply search filter if specified
                                event_name = f"{event.get('localteam', {}).get('name', 'Unknown')} vs {event.get('awayteam', {}).get('name', 'Unknown')}"
                                if search_term and search_term.lower() not in event_name.lower() and search_term.lower() not in str(event_id).lower():
                                    continue
                                
                                # Add to sports and markets filters
                                all_sports.add(sport_display_name)
                                all_markets.add(market_name)
                                
                                # Create betting event entry
                                betting_event = {
                                    'id': f"{event_id}_{market_id}",
                                    'unique_id': f"{event_id}_{market_id}",
                                    'event_id': f"{event_id}_{market_id}",
                                    'sport': sport_display_name,
                                    'event_name': event_name,
                                    'market': market_name,
                                    'market_display': market_name,
                                    'category': event.get('_category_name', 'Unknown Category'),
                                    'odds_data': [],  # We'll populate this if needed
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
                                
                                # Calculate global financials for this event (across all operators)
                                max_liability, max_possible_gain = calculate_global_event_financials(event_id, market_id, sport_folder)
                                betting_event['max_liability'] = max_liability
                                betting_event['max_possible_gain'] = max_possible_gain
                                
                                # Add fields expected by the dashboard
                                betting_event['name'] = event_name
                                betting_event['liability'] = max_liability
                                betting_event['revenue'] = max_possible_gain
                                
                                # Get total bets for this event across all operators
                                bet_count_result = conn.execute("""
                                    SELECT COUNT(*) as count
                                    FROM bets b 
                                    JOIN users u ON b.user_id = u.id 
                                    JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
                                    WHERE op.is_active = 1 AND b.match_id = ? AND b.sport_name = ? AND b.market = ?
                                """, (event_id, sport_folder, market_id)).fetchone()
                                total_bets = bet_count_result['count'] if bet_count_result else 0
                                betting_event['total_bets'] = total_bets
                                
                                all_events.append(betting_event)
                                
                except Exception as e:
                    print(f"Error loading events for {sport_folder}: {e}")
                    continue
        
        conn.close()
        
        # Calculate global summary
        total_events = len(all_events)
        active_events = len([e for e in all_events if e['status'] == 'active'])
        max_liability = max([e['liability'] for e in all_events]) if all_events else 0
        max_gain = max([e['revenue'] for e in all_events]) if all_events else 0
        
        sports = list(all_sports)
        markets = list(all_markets)
        
        return jsonify({
            'success': True,
            'events': all_events,
            'pagination': {
            'page': 1,
                'per_page': len(all_events),
                'total': total_events,
                'pages': 1
            },
            'summary': {
                'total_events': total_events,  # Show total available events, not filtered count
                'active_events': active_events,  # Count from all events
                'total_liability': max_liability,
                'max_liability': max_liability,
                'max_possible_gain': max_gain
            },
            'filters': {
                'sports': sports,
                'markets': markets
            }
        })
        
    except Exception as e:
        print(f"Error fetching global betting events: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/global-betting-events/toggle-status', methods=['POST'])
@check_superadmin_auth
def toggle_global_event_status():
    """Toggle the status of a global betting event"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        new_status = data.get('status')
        
        if not event_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing event_id or status'}), 400
            
        conn = get_db_connection()
        
        # Since we don't have a separate betting_events table, we'll update the bets table
        # to mark bets for this event as inactive/active
        if new_status == 'inactive':
            # Mark all bets for this event as inactive
            result = conn.execute("""
                UPDATE bets 
                SET is_active = 0 
                WHERE match_id = ?
            """, (event_id,))
        else:
            # Mark all bets for this event as active
            result = conn.execute("""
                UPDATE bets 
                SET is_active = 1 
                WHERE match_id = ?
            """, (event_id,))
        
        conn.commit()
        conn.close()
        
        if result.rowcount > 0:
            return jsonify({'success': True, 'message': f'Event status updated to {new_status}'})
        else:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
            
    except Exception as e:
        print(f"Error toggling global event status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/global-users')
@check_superadmin_auth
def get_global_users():
    """Get all users across all operators"""
    
    try:
        conn = get_db_connection()
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Get all users with operator information
        users_query = """
        SELECT u.id, u.username, u.email, u.balance, u.created_at, u.is_active,
               so.sportsbook_name as operator_name,
               (SELECT COUNT(*) FROM bets WHERE user_id = u.id) as total_bets,
               (SELECT COALESCE(SUM(stake), 0) FROM bets WHERE user_id = u.id) as total_staked,
               (SELECT COALESCE(SUM(potential_return), 0) FROM bets WHERE user_id = u.id AND status = 'won') as total_payout,
               (SELECT COALESCE(SUM(stake), 0) - COALESCE(SUM(potential_return), 0) FROM bets WHERE user_id = u.id AND status IN ('won', 'lost')) as profit
        FROM users u
        LEFT JOIN sportsbook_operators so ON u.sportsbook_operator_id = so.id
        ORDER BY u.created_at DESC
        LIMIT ? OFFSET ?
        """
        
        users = conn.execute(users_query, (per_page, offset)).fetchall()
        
        # Get total count
        total_count = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'users': [dict(user) for user in users],
            'total': total_count,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/operators')
@check_superadmin_auth
def get_operators():
    """Get all sportsbook operators"""
    
    try:
        conn = get_db_connection()
        
        operators_query = """
        SELECT so.id, so.sportsbook_name, so.subdomain, so.login, so.email, 
               so.created_at, so.is_active,
               (SELECT COUNT(*) FROM users WHERE sportsbook_operator_id = so.id) as user_count,
               (SELECT COUNT(*) FROM bets b JOIN users u ON b.user_id = u.id WHERE u.sportsbook_operator_id = so.id) as bet_count,
               (SELECT COALESCE(SUM(stake), 0) - COALESCE(SUM(potential_return), 0) FROM bets b JOIN users u ON b.user_id = u.id WHERE u.sportsbook_operator_id = so.id AND b.status IN ('won', 'lost')) as revenue
        FROM sportsbook_operators so
        ORDER BY so.created_at DESC
        """
        
        operators = conn.execute(operators_query).fetchall()
        conn.close()
        
        return jsonify({
            'operators': [dict(op) for op in operators]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/user/<int:user_id>/toggle', methods=['POST'])
@check_superadmin_auth
def toggle_global_user_status(user_id):
    """Toggle user status globally (super admin power)"""
    
    try:
        conn = get_db_connection()
        
        # Get user
        user = conn.execute("SELECT id, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Toggle status
        new_status = not user['is_active']
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f"User {'enabled' if new_status else 'disabled'} globally",
            'new_status': new_status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/operator/<int:operator_id>/toggle', methods=['POST'])
@check_superadmin_auth
def toggle_operator_status(operator_id):
    """Toggle operator status (enable/disable)"""
    
    try:
        conn = get_db_connection()
        
        # Get current operator status
        operator = conn.execute('SELECT * FROM sportsbook_operators WHERE id = ?', (operator_id,)).fetchone()
        if not operator:
            conn.close()
            return jsonify({'error': 'Operator not found'}), 404
        
        # Toggle status
        new_status = not operator['is_active']
        conn.execute('UPDATE sportsbook_operators SET is_active = ? WHERE id = ?', (new_status, operator_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'new_status': new_status})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/global-stats')
@check_superadmin_auth
def get_global_stats():
    """Get global statistics for the super admin dashboard (adapted from admin interface)"""
    try:
        conn = get_db_connection()
        
        # Get total operators count
        operator_count = conn.execute(
            "SELECT COUNT(*) as count FROM sportsbook_operators WHERE is_active = 1"
        ).fetchone()['count']
        
        # Get total users count across all operators
        user_count = conn.execute("""
            SELECT COUNT(*) as count 
            FROM users u 
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id 
            WHERE op.is_active = 1
        """).fetchone()['count']
        
        # Get total bets count across all operators
        bet_count = conn.execute("""
            SELECT COUNT(*) as count 
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
            WHERE op.is_active = 1
        """).fetchone()['count']
        
        # Get total revenue across all operators (from won bets)
        revenue_result = conn.execute("""
            SELECT COALESCE(SUM(b.potential_return - b.stake), 0) as revenue
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
            WHERE op.is_active = 1 AND b.status = 'won'
        """).fetchone()
        total_revenue = float(revenue_result['revenue'] or 0)
        
        # Get active events count across all operators (events with pending bets)
        active_events_result = conn.execute("""
            SELECT COUNT(DISTINCT b.match_id) as count
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
            WHERE op.is_active = 1 AND b.status = 'pending'
        """).fetchone()
        active_events = active_events_result['count']
        
        # Get total liability across all operators (sum of all pending bet potential returns)
        # This matches the calculation shown in the betting events table
        liability_result = conn.execute("""
            SELECT COALESCE(SUM(b.potential_return), 0) as liability
            FROM bets b 
            JOIN users u ON b.user_id = u.id 
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
            WHERE op.is_active = 1 AND b.status = 'pending'
        """).fetchone()
        total_liability = float(liability_result['liability'] or 0)
        
        conn.close()
        
        return jsonify({
            'total_operators': operator_count,
            'total_users': user_count,
            'total_bets': bet_count,
            'total_revenue': total_revenue,
            'active_events': active_events,
            'total_liability': total_liability
        })
        
    except Exception as e:
        print(f"Error getting global stats: {e}")
        return jsonify({'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/global-reports/overview')
@check_superadmin_auth
def get_global_reports_overview():
    """Get comprehensive global reports overview across all operators"""
    
    try:
        conn = get_db_connection()
        
        # Total bets and revenue across all operators
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
        JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
        WHERE op.is_active = 1
        """
        
        totals = conn.execute(total_query).fetchone()
        
        # Daily revenue for the last 30 days across all operators
        daily_query = """
        SELECT 
            DATE(b.created_at) as bet_date,
            COUNT(*) as daily_bets,
            SUM(b.stake) as daily_stakes,
            SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
            SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as daily_revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
        WHERE op.is_active = 1 AND b.created_at >= date('now', '-30 days')
        GROUP BY DATE(b.created_at)
        ORDER BY bet_date DESC
        """
        
        daily_data = conn.execute(daily_query).fetchall()
        
        # Sport-wise performance across all operators
        sport_query = """
        SELECT 
            b.sport_name,
            COUNT(*) as bets_count,
            SUM(b.stake) as total_stakes,
            SUM(CASE WHEN b.status = 'lost' THEN b.stake ELSE 0 END) - 
            SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as sport_revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
        WHERE op.is_active = 1
        GROUP BY b.sport_name
        ORDER BY sport_revenue DESC
        """
        
        sport_data = conn.execute(sport_query).fetchall()
        
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

@rich_superadmin_bp.route('/superadmin/api/global-reports/generate', methods=['POST'])
@check_superadmin_auth
def generate_global_custom_report():
    """Generate custom global reports based on parameters across all operators"""
    
    try:
        data = request.get_json()
        report_type = data.get('report_type', 'revenue')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        sport_filter = data.get('sport_filter')
        group_by = data.get('group_by', 'day')
        
        conn = get_db_connection()
        
        # Build base query with global filtering (all active operators)
        base_where = "op.is_active = 1"
        params = []
        
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
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
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
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
            WHERE op.is_active = 1
            GROUP BY u.id, u.username, u.email, u.created_at
            ORDER BY total_bets DESC
            """
            params = []  # Reset params for user query
            
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
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
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
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
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
        print(f"Error generating global custom report: {e}")
        return jsonify({'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/global-reports/available-sports')
@check_superadmin_auth
def get_global_available_sports_for_reports():
    """Get available sports for global report filtering across all operators"""
    
    try:
        conn = get_db_connection()
        
        # Get sports that have bets from all active operators
        sports_query = """
        SELECT DISTINCT b.sport_name
        FROM bets b
        JOIN users u ON b.user_id = u.id
        JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
        WHERE op.is_active = 1 AND b.sport_name IS NOT NULL AND b.sport_name != ''
        ORDER BY b.sport_name
        """
        
        sports_result = conn.execute(sports_query).fetchall()
        conn.close()
        
        sports = [row['sport_name'] for row in sports_result]
        
        return jsonify({'sports': sports})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rich_superadmin_bp.route('/superadmin/api/global-reports/export', methods=['POST'])
@check_superadmin_auth
def export_global_custom_report():
    """Export global custom report to CSV across all operators"""
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        report_type = data.get('report_type', 'revenue')
        format_type = data.get('format', 'csv')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        sport_filter = data.get('sport_filter')
        
        print(f"DEBUG: Global export request - type: {report_type}, format: {format_type}, from: {date_from}, to: {date_to}, sport: {sport_filter}")
        
        conn = get_db_connection()
        
        # Build base query (similar to generate endpoint)
        base_where = "op.is_active = 1"
        params = []
        
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
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
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
            JOIN sportsbook_operators op ON u.sportsbook_operator_id = op.id
            WHERE op.is_active = 1
            GROUP BY u.id, u.username, u.email, u.created_at
            ORDER BY total_bets DESC
            """
            headers = ['Username', 'Email', 'Total Bets', 'Total Staked', 'Payout', 'Profit', 'Join Date']
            params = []
        
        else:
            return jsonify({'error': 'Export not supported for this report type'}), 400
        
        # Execute query
        try:
            result = conn.execute(query, params).fetchall()
            print(f"DEBUG: Global query executed successfully, got {len(result)} rows")
        except Exception as query_error:
            print(f"DEBUG: Global query execution error: {query_error}")
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
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_global_report.csv'
        return response
        
    except Exception as e:
        print(f"Error exporting global report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Rich Super Admin Template (same rich interface as original admin_app.py but global)
RICH_SUPERADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GoalServe - Super Admin Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
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
            background: #e67e22;
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
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            font-weight: 500;
        }
        
        .summary-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .controls {
            margin-bottom: 20px;
        }
        
        .controls button {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .controls button:hover {
            background: #2980b9;
        }
        
        .report-builder-form {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .form-actions {
            display: flex;
            gap: 15px;
            margin-top: 25px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        
        .btn-primary {
            background: #27ae60;
            color: white;
        }
        
        .btn-primary:hover {
            background: #229954;
        }
        
        .btn-secondary {
            background: #95a5a6;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #7f8c8d;
        }
        
        .report-results {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        
        .report-results h3 {
            margin: 0 0 20px 0;
            color: #2c3e50;
        }
        
        .positive {
            color: #27ae60;
            font-weight: 500;
        }
        
        .negative {
            color: #e74c3c;
            font-weight: 500;
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
            margin-right: 0.5rem;
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
        
        .operator-name {
            font-weight: 600;
            color: #e67e22;
        }

        /* Global Betting Events Management Styles */
        .section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 16px;
            font-weight: 600;
            opacity: 1;
            color: white;
        }

        .summary-card p {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }

        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        .controls select,
        .controls input[type="text"] {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        .controls label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .controls input[type="checkbox"] {
            margin: 0;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: #28a745;
            color: white;
        }

        .btn-primary:hover {
            background: #218838;
        }

        .btn-danger {
            background: #dc3545;
            color: white;
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn-success {
            background: #28a745;
            color: white;
        }

        .btn-success:hover {
            background: #218838;
        }

        .btn-sm {
            padding: 4px 8px;
            font-size: 12px;
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }

        .status-badge.active {
            background: #d4edda;
            color: #155724;
        }

        .status-badge.disabled {
            background: #f8d7da;
            color: #721c24;
        }

        .positive {
            color: #28a745;
        }

        .negative {
            color: #dc3545;
        }

        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }

        .error {
            text-align: center;
            color: #dc3545;
            font-weight: 500;
        }

        .no-data {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        
        /* Hide welcome banners */
        .welcome-banner {
            display: none !important;
        }
        
        /* Hide any other welcome messages */
        .welcome-message,
        .welcome-header,
        [class*="welcome"] {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌟 GoalServe - Super Admin Dashboard</h1>
        <div class="admin-info">
            <span>Global Management</span>
            <a href="/superadmin/logout" class="logout-btn">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showSection('global-overview')">🏠 Global Overview</button>
            <button class="nav-tab" onclick="showSection('global-betting-events')">📊 Global Betting Events</button>
            <button class="nav-tab" onclick="showSection('global-user-management')">👥 Global User Management</button>
            <button class="nav-tab" onclick="showSection('global-reports')">📈 Global Reports</button>
            <button class="nav-tab" onclick="showSection('operator-management')">🏢 Operator Management</button>
            <button class="nav-tab" onclick="showSection('global-report-builder')">🔧 Global Report Builder</button>
        </div>
        
        <!-- Global Dashboard Overview -->
        <div id="global-overview" class="section active">
            <h2>Global Dashboard Overview</h2>
            <p>Comprehensive view of all sportsbook operators and their performance</p>
            
            <!-- Global Summary Cards -->
            <div class="summary-cards">
                <div class="summary-card">
                    <h3>Total Operators</h3>
                    <p id="global-total-operators">0</p>
                </div>
                <div class="summary-card">
                    <h3>Total Users</h3>
                    <p id="global-total-users">0</p>
                </div>
                <div class="summary-card">
                    <h3>Total Bets</h3>
                    <p id="global-total-bets">0</p>
                </div>
                <div class="summary-card">
                    <h3>Total Revenue</h3>
                    <p id="global-total-revenue">$0.00</p>
                </div>
                <div class="summary-card">
                    <h3>Active Events</h3>
                    <p id="global-active-events">0</p>
                </div>
                <div class="summary-card">
                    <h3>Total Liability</h3>
                    <p id="global-total-liability">$0.00</p>
                </div>
                </div>
            </div>
            
        <!-- Global Betting Events Management -->
        <div id="global-betting-events" class="section">
            <h2>Global Betting Events Management</h2>
            


            <!-- Controls -->
            <div class="controls">
                <select id="global-sport-filter">
                    <option value="">All Sports</option>
                </select>
                <select id="global-market-filter">
                    <option value="">All Markets</option>
                </select>
                <input type="text" id="global-event-search" placeholder="Search events...">
                <label>
                    <input type="checkbox" id="global-show-bets-only" checked>
                    Show Only Events with Bets (Faster)
                </label>
                <button onclick="refreshGlobalEvents()" class="btn btn-primary">
                    <i class="fas fa-sync-alt"></i> Refresh Events
                </button>
            </div>
            
                         <!-- Events Table -->
            <div class="table-container">
                <table id="global-events-table">
                    <thead>
                        <tr>
                             <th onclick="sortTable('global-events-table', 0)" style="cursor: pointer;">
                                 Event ID <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-events-table', 1)" style="cursor: pointer;">
                                 Sport <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-events-table', 2)" style="cursor: pointer;">
                                 Event Name <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-events-table', 3)" style="cursor: pointer;">
                                 Market <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-events-table', 4)" style="cursor: pointer;">
                                 Total Bets <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-events-table', 5)" style="cursor: pointer;">
                                 Liability <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-events-table', 6)" style="cursor: pointer;">
                                 Revenue <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-events-table', 7)" style="cursor: pointer;">
                                 Status <span class="sort-icon">↕</span>
                             </th>
                             <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="global-events-tbody">
                         <!-- Events will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Global User Management Section -->
        <div id="global-user-management" class="content-section">
            <h2>Global User Management</h2>
            <p>Manage users across all sportsbook operators with global admin powers</p>
            
            <div class="controls">
                <button onclick="loadGlobalUsers()">🔄 Refresh Global Users</button>
            </div>
            
            <div class="table-container">
                <table id="global-users-table">
                    <thead>
                        <tr>
                             <th onclick="sortTable('global-users-table', 0)" style="cursor: pointer;">
                                 ID <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 1)" style="cursor: pointer;">
                                 Username <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 2)" style="cursor: pointer;">
                                 Email <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 3)" style="cursor: pointer;">
                                 Operator <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 4)" style="cursor: pointer;">
                                 Balance <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 5)" style="cursor: pointer;">
                                 Bets <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 6)" style="cursor: pointer;">
                                 Staked <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 7)" style="cursor: pointer;">
                                 Payout <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 8)" style="cursor: pointer;">
                                 Profit <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 9)" style="cursor: pointer;">
                                 Joined <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('global-users-table', 10)" style="cursor: pointer;">
                                 Status <span class="sort-icon">↕</span>
                             </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="global-users-tbody">
                        <tr><td colspan="12" class="loading">Loading global users...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Operator Management Section -->
        <div id="operator-management" class="content-section">
            <h2>🏢 Operator Management</h2>
            <p>Manage all sportsbook operators - enable/disable entire sportsbooks</p>
            
            <div class="controls">
                <button onclick="loadOperators()">🔄 Refresh Operators</button>
            </div>
            
            <div class="table-container">
                <table id="operators-table">
                    <thead>
                        <tr>
                             <th onclick="sortTable('operators-table', 0)" style="cursor: pointer;">
                                 ID <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 1)" style="cursor: pointer;">
                                 Sportsbook Name <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 2)" style="cursor: pointer;">
                                 Subdomain <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 3)" style="cursor: pointer;">
                                 Admin Username <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 4)" style="cursor: pointer;">
                                 Admin Email <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 5)" style="cursor: pointer;">
                                 Users <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 6)" style="cursor: pointer;">
                                 Bets <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 7)" style="cursor: pointer;">
                                 Revenue <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 8)" style="cursor: pointer;">
                                 Created <span class="sort-icon">↕</span>
                             </th>
                             <th onclick="sortTable('operators-table', 9)" style="cursor: pointer;">
                                 Status <span class="sort-icon">↕</span>
                             </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="operators-tbody">
                        <tr><td colspan="11" class="loading">Loading operators...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Global Reports Section -->
        <div id="global-reports" class="content-section">
            <h2>Global Reports & Analytics</h2>
            <p>Comprehensive reporting across all sportsbook operations</p>
            
            <div class="summary-cards">
                <div class="summary-card">
                    <h3>Total Bets</h3>
                    <div class="value" id="global-total-bets">0</div>
                </div>
                <div class="summary-card">
                    <h3>Total Stakes</h3>
                    <div class="value" id="global-total-stakes">$0.00</div>
                </div>
                <div class="summary-card">
                    <h3>Global Revenue</h3>
                    <div class="value" id="global-total-revenue">$0.00</div>
                </div>
                <div class="summary-card">
                    <h3>Win Rate</h3>
                    <div class="value" id="global-win-rate">0%</div>
                </div>
            </div>
            
            <div class="controls">
                <button onclick="loadGlobalReports()">🔄 Refresh Global Reports</button>
            </div>
            
            <div class="table-container">
                <table id="global-reports-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Sport</th>
                            <th>Total Bets</th>
                            <th>Total Stakes</th>
                            <th>Revenue</th>
                        </tr>
                    </thead>
                    <tbody id="global-reports-tbody">
                        <tr><td colspan="5" class="loading">Loading global reports...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Global Report Builder Section -->
        <div id="global-report-builder" class="content-section">
            <h2>🔧 Global Report Builder</h2>
            <p>Create custom reports across all sportsbooks</p>
            
            <div class="report-builder-form">
                <div class="form-group">
                    <label for="global-report-type">Report Type:</label>
                    <select id="global-report-type">
                        <option value="revenue">Revenue Report</option>
                        <option value="user-activity">User Activity Report</option>
                        <option value="betting-patterns">Betting Patterns Report</option>
                        <option value="sport-performance">Sport Performance Report</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="global-date-from">Date From:</label>
                    <input type="date" id="global-date-from">
                </div>
                
                <div class="form-group">
                    <label for="global-date-to">Date To:</label>
                    <input type="date" id="global-date-to">
                </div>
                
                <div class="form-group">
                    <label for="global-sport-filter">Sport Filter:</label>
                    <select id="global-sport-filter">
                        <option value="">All Sports</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="global-group-by">Group By:</label>
                    <select id="global-group-by">
                        <option value="day">Day</option>
                        <option value="week">Week</option>
                        <option value="month">Month</option>
                        <option value="sport">Sport</option>
                    </select>
                </div>
                
                <div class="form-actions">
                    <button onclick="generateGlobalReport()" class="btn btn-primary">📊 Generate Report</button>
                    <button onclick="exportGlobalReport()" class="btn btn-secondary">📥 Export CSV</button>
                </div>
            </div>
            
            <div class="report-results" id="global-report-results" style="display: none;">
                <h3>📋 Report Results</h3>
                <div class="table-container">
                    <table id="global-report-table">
                        <thead id="global-report-header">
                        </thead>
                        <tbody id="global-report-body">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showSection(sectionId) {
            // Hide all sections
            document.querySelectorAll('.section, .content-section').forEach(section => {
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
            
            // Load data for the section
            if (sectionId === 'global-overview') {
                loadGlobalStats();
            } else if (sectionId === 'global-betting-events') {
                loadGlobalBettingEvents();
            } else if (sectionId === 'global-user-management') {
                loadGlobalUsers();
            } else if (sectionId === 'global-reports') {
                loadGlobalReports();
            } else if (sectionId === 'operator-management') {
                loadOperators();
            } else if (sectionId === 'global-report-builder') {
                loadGlobalReportBuilder();
            }
        }
        
        async function loadGlobalBettingEvents() {
            try {
                const response = await fetch('/superadmin/api/global-betting-events');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('global-events-tbody').innerHTML = 
                        `<tr><td colspan="9" class="error">Error: ${data.error}</td></tr>`;
                    return;
                }
                
                // Update summary cards
                document.getElementById('global-total-events').textContent = data.total || 0;
                document.getElementById('global-active-events').textContent = data.events.length || 0;
                
                // Update table
                const tbody = document.getElementById('global-events-tbody');
                if (data.events.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" class="loading">No events found</td></tr>';
                } else {
                    tbody.innerHTML = data.events.map(event => `
                        <tr>
                            <td>${event.event_id}</td>
                            <td>${event.sport}</td>
                            <td>${event.event_name}</td>
                            <td>${event.market}</td>
                            <td><span class="operator-name">${event.operator_name || 'Unknown'}</span></td>
                            <td>${event.total_bets || 0}</td>
                            <td class="liability">$${event.liability || '0.00'}</td>
                            <td class="revenue">$${event.revenue || '0.00'}</td>
                            <td><span class="status-badge status-${event.status}">${event.status}</span></td>
                        </tr>
                    `).join('');
                }
                
            } catch (error) {
                document.getElementById('global-events-tbody').innerHTML = 
                    `<tr><td colspan="9" class="error">Error loading events: ${error.message}</td></tr>`;
            }
        }
        
        async function loadGlobalUsers() {
            try {
                const response = await fetch('/superadmin/api/global-users');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('global-users-tbody').innerHTML = 
                        `<tr><td colspan="12" class="error">Error: ${data.error}</td></tr>`;
                    return;
                }
                
                const tbody = document.getElementById('global-users-tbody');
                if (data.users.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="12" class="loading">No users found</td></tr>';
                } else {
                    tbody.innerHTML = data.users.map(user => `
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.username}</td>
                            <td>${user.email}</td>
                            <td><span class="operator-name">${user.operator_name || 'Default Sportsbook'}</span></td>
                            <td>$${user.balance}</td>
                            <td>${user.total_bets}</td>
                            <td>$${user.total_staked}</td>
                            <td>$${user.total_payout}</td>
                            <td>$${user.profit}</td>
                            <td>${new Date(user.created_at).toLocaleDateString()}</td>
                            <td><span class="status-badge status-${user.is_active ? 'active' : 'disabled'}">${user.is_active ? 'Active' : 'Disabled'}</span></td>
                            <td>
                                <button class="action-btn ${user.is_active ? 'btn-disable' : 'btn-enable'}" 
                                        onclick="toggleGlobalUserStatus(${user.id})">
                                    ${user.is_active ? 'Disable' : 'Enable'}
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
                
            } catch (error) {
                document.getElementById('global-users-tbody').innerHTML = 
                    `<tr><td colspan="12" class="error">Error loading users: ${error.message}</td></tr>`;
            }
        }
        
        async function loadOperators() {
            try {
                const response = await fetch('/superadmin/api/operators');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('operators-tbody').innerHTML = 
                        `<tr><td colspan="11" class="error">Error: ${data.error}</td></tr>`;
                    return;
                }
                
                const tbody = document.getElementById('operators-tbody');
                if (data.operators.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="11" class="loading">No operators found</td></tr>';
                } else {
                    tbody.innerHTML = data.operators.map(op => `
                        <tr>
                            <td>${op.id}</td>
                            <td><span class="operator-name">${op.sportsbook_name}</span></td>
                            <td>${op.subdomain}</td>
                            <td>${op.login}</td>
                            <td>${op.email}</td>
                            <td>${op.user_count}</td>
                            <td>${op.bet_count}</td>
                            <td>$${op.revenue.toFixed(2)}</td>
                            <td>${new Date(op.created_at).toLocaleDateString()}</td>
                            <td><span class="status-badge status-${op.is_active ? 'active' : 'disabled'}">${op.is_active ? 'Active' : 'Disabled'}</span></td>
                            <td>
                                <button class="action-btn ${op.is_active ? 'btn-disable' : 'btn-enable'}" 
                                        onclick="toggleOperatorStatus(${op.id})">
                                    ${op.is_active ? 'Disable' : 'Enable'}
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
                
            } catch (error) {
                document.getElementById('operators-tbody').innerHTML = 
                    `<tr><td colspan="11" class="error">Error loading operators: ${error.message}</td></tr>`;
            }
        }
        
        async function loadGlobalReports() {
            try {
                const response = await fetch('/superadmin/api/global-reports/overview');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('global-reports-tbody').innerHTML = 
                        `<tr><td colspan="5" class="error">Error: ${data.error}</td></tr>`;
                    return;
                }
                
                // Update summary cards
                document.getElementById('global-total-bets').textContent = data.overview.total_bets || 0;
                document.getElementById('global-total-stakes').textContent = `$${(data.overview.total_stakes || 0).toFixed(2)}`;
                document.getElementById('global-total-revenue').textContent = `$${(data.overview.total_revenue || 0).toFixed(2)}`;
                document.getElementById('global-win-rate').textContent = `${(data.overview.win_rate || 0).toFixed(1)}%`;
                
                // Update table
                const tbody = document.getElementById('global-reports-tbody');
                if (data.daily_data && data.daily_data.length > 0) {
                    tbody.innerHTML = data.daily_data.map(row => `
                        <tr>
                            <td>${row.bet_date}</td>
                            <td>${row.sport_name || 'All Sports'}</td>
                            <td>${row.daily_bets || 0}</td>
                            <td>$${(row.daily_stakes || 0).toFixed(2)}</td>
                            <td class="${(row.daily_revenue || 0) >= 0 ? 'positive' : 'negative'}">$${(row.daily_revenue || 0).toFixed(2)}</td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" class="loading">No report data available</td></tr>';
                }
                
            } catch (error) {
                document.getElementById('global-reports-tbody').innerHTML = 
                    `<tr><td colspan="5" class="error">Error loading reports: ${error.message}</td></tr>`;
            }
        }
        
        async function loadGlobalReportBuilder() {
            try {
                // Load available sports for filtering
                const response = await fetch('/superadmin/api/global-reports/available-sports');
                const data = await response.json();
                
                if (data.sports) {
                    const sportSelect = document.getElementById('global-sport-filter');
                    sportSelect.innerHTML = '<option value="">All Sports</option>';
                    data.sports.forEach(sport => {
                        sportSelect.innerHTML += `<option value="${sport}">${sport}</option>`;
                    });
                }
                
                // Set default dates (last 30 days)
                const today = new Date();
                const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
                
                document.getElementById('global-date-from').value = thirtyDaysAgo.toISOString().split('T')[0];
                document.getElementById('global-date-to').value = today.toISOString().split('T')[0];
                
            } catch (error) {
                console.error('Error loading report builder:', error);
            }
        }
        
        async function generateGlobalReport() {
            try {
                const reportType = document.getElementById('global-report-type').value;
                const dateFrom = document.getElementById('global-date-from').value;
                const dateTo = document.getElementById('global-date-to').value;
                const sportFilter = document.getElementById('global-sport-filter').value;
                const groupBy = document.getElementById('global-group-by').value;
                
                const requestData = {
                    report_type: reportType,
                    date_from: dateFrom,
                    date_to: dateTo,
                    sport_filter: sportFilter,
                    group_by: groupBy
                };
                
                const response = await fetch('/superadmin/api/global-reports/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });
                
                const data = await response.json();
                
                if (data.error) {
                    alert('Error generating report: ' + data.error);
                    return;
                }
                
                // Display report results
                displayGlobalReportResults(data, reportType);
                
            } catch (error) {
                alert('Error generating report: ' + error.message);
            }
        }
        
        function displayGlobalReportResults(data, reportType) {
            const resultsDiv = document.getElementById('global-report-results');
            const header = document.getElementById('global-report-header');
            const body = document.getElementById('global-report-body');
            
            // Show results section
            resultsDiv.style.display = 'block';
            
            // Set headers based on report type
            let headers = [];
            if (reportType === 'revenue') {
                headers = ['Date', 'Sport', 'Total Bets', 'Total Stakes', 'Revenue'];
            } else if (reportType === 'user-activity') {
                headers = ['Username', 'Email', 'Total Bets', 'Total Staked', 'Payout', 'Profit', 'Join Date'];
            } else if (reportType === 'betting-patterns') {
                headers = ['Date', 'Sport', 'Bet Type', 'Count', 'Total Amount', 'Win Rate'];
            } else if (reportType === 'sport-performance') {
                headers = ['Sport', 'Total Bets', 'Total Stakes', 'Won Bets', 'Lost Bets', 'Revenue', 'Win Rate'];
            }
            
            // Create header row
            header.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
            
            // Create body rows
            if (data.length === 0) {
                body.innerHTML = '<tr><td colspan="' + headers.length + '" class="loading">No data available for selected criteria</td></tr>';
            } else {
                body.innerHTML = data.map(row => {
                    const cells = headers.map(header => {
                        let value = '';
                        if (header === 'Date' && row.bet_date) {
                            value = row.bet_date;
                        } else if (header === 'Sport' && row.sport_name) {
                            value = row.sport_name;
                        } else if (header === 'Total Bets' && row.total_bets !== undefined) {
                            value = row.total_bets;
                        } else if (header === 'Total Stakes' && row.total_stakes !== undefined) {
                            value = `$${(row.total_stakes || 0).toFixed(2)}`;
                        } else if (header === 'Revenue' && row.revenue !== undefined) {
                            const revenueClass = (row.revenue || 0) >= 0 ? 'positive' : 'negative';
                            value = `<span class="${revenueClass}">$${(row.revenue || 0).toFixed(2)}</span>`;
                        } else if (header === 'Username' && row.username) {
                            value = row.username;
                        } else if (header === 'Email' && row.email) {
                            value = row.email;
                        } else if (header === 'Total Staked' && row.total_staked !== undefined) {
                            value = `$${(row.total_staked || 0).toFixed(2)}`;
                        } else if (header === 'Payout' && row.payout !== undefined) {
                            value = `$${(row.payout || 0).toFixed(2)}`;
                        } else if (header === 'Profit' && row.user_profit !== undefined) {
                            const profitClass = (row.user_profit || 0) >= 0 ? 'positive' : 'negative';
                            value = `<span class="${profitClass}">$${(row.user_profit || 0).toFixed(2)}</span>`;
                        } else if (header === 'Join Date' && row.joined_date) {
                            value = new Date(row.joined_date).toLocaleDateString();
                        } else if (header === 'Bet Type' && row.bet_type) {
                            value = row.bet_type;
                        } else if (header === 'Count' && row.count !== undefined) {
                            value = row.count;
                        } else if (header === 'Total Amount' && row.total_amount !== undefined) {
                            value = `$${(row.total_amount || 0).toFixed(2)}`;
                        } else if (header === 'Win Rate' && row.win_rate !== undefined) {
                            value = `${(row.win_rate || 0).toFixed(1)}%`;
                        } else if (header === 'Won Bets' && row.won_bets !== undefined) {
                            value = row.won_bets;
                        } else if (header === 'Lost Bets' && row.lost_bets !== undefined) {
                            value = row.lost_bets;
                        } else {
                            value = row[Object.keys(row).find(key => key.toLowerCase().includes(header.toLowerCase().replace(' ', '_')))] || '';
                        }
                        return `<td>${value}</td>`;
                    });
                    return `<tr>${cells.join('')}</tr>`;
                }).join('');
            }
        }
        
        async function exportGlobalReport() {
            try {
                const reportType = document.getElementById('global-report-type').value;
                const dateFrom = document.getElementById('global-date-from').value;
                const dateTo = document.getElementById('global-date-to').value;
                const sportFilter = document.getElementById('global-sport-filter').value;
                
                const requestData = {
                    report_type: reportType,
                    date_from: dateFrom,
                    date_to: dateTo,
                    sport_filter: sportFilter,
                    format: 'csv'
                };
                
                const response = await fetch('/superadmin/api/global-reports/export', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (response.ok) {
                    // Create download link
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${reportType}_global_report.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    const errorData = await response.json();
                    alert('Error exporting report: ' + (errorData.error || 'Unknown error'));
                }
                
            } catch (error) {
                alert('Error exporting report: ' + error.message);
            }
        }
        
        async function toggleGlobalUserStatus(userId) {
            try {
                const response = await fetch(`/superadmin/api/user/${userId}/toggle`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    loadGlobalUsers(); // Reload the users table
                } else {
                    alert('Error: ' + data.error);
                }
                
            } catch (error) {
                alert('Error toggling user status: ' + error.message);
            }
        }
        
        async function toggleOperatorStatus(operatorId) {
            try {
                const response = await fetch(`/superadmin/api/operator/${operatorId}/toggle`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    loadOperators(); // Reload the operators table
                } else {
                    alert('Error: ' + data.error);
                }
                
            } catch (error) {
                alert('Error toggling operator status: ' + error.message);
            }
        }
        
        // Global Betting Events Management Functions
        function loadGlobalBettingEvents() {
            const sportFilter = document.getElementById('global-sport-filter').value;
            const marketFilter = document.getElementById('global-market-filter').value;
            const searchTerm = document.getElementById('global-event-search').value;
            const showBetsOnly = document.getElementById('global-show-bets-only').checked;

                         // Show loading state
             document.getElementById('global-events-tbody').innerHTML = '<tr><td colspan="9" class="loading">Loading global events...</td></tr>';

            fetch('/superadmin/api/global-betting-events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sport: sportFilter,
                    market: marketFilter,
                    search: searchTerm,
                    show_bets_only: showBetsOnly
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayGlobalEvents(data.events);
                    // Update total liability in summary card from table data
                    if (document.getElementById('global-total-liability')) {
                        document.getElementById('global-total-liability').textContent = '$' + (data.summary.total_liability || 0).toFixed(2);
                    }
                    loadGlobalSportsFilter(data.filters.sports);
                    loadGlobalMarketsFilter(data.filters.markets);
                } else {
                    document.getElementById('global-events-tbody').innerHTML = '<tr><td colspan="9" class="error">Error loading events: ' + data.error + '</td></tr>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('global-events-tbody').innerHTML = '<tr><td colspan="9" class="error">Failed to load events</td></tr>';
            });
        }

        function refreshGlobalEvents() {
            loadGlobalBettingEvents();
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

        function displayGlobalEvents(events) {
            const tbody = document.getElementById('global-events-tbody');
            tbody.innerHTML = '';

            if (events.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="no-data">No events found</td></tr>';
                return;
            }

            events.forEach(event => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td data-sort="${event.event_id}">${event.event_id}</td>
                    <td data-sort="${event.sport}">${event.sport}</td>
                    <td data-sort="${event.event_name}">${event.event_name}</td>
                    <td data-sort="${event.market}">${event.market}</td>
                    <td data-sort="${event.total_bets}">${event.total_bets}</td>
                    <td data-sort="${event.liability}" class="${event.liability < 0 ? 'negative' : 'positive'}">$${Math.abs(event.liability).toFixed(2)}</td>
                    <td data-sort="${event.revenue}" class="${event.revenue < 0 ? 'negative' : 'positive'}">$${Math.abs(event.revenue).toFixed(2)}</td>
                    <td data-sort="${event.status}"><span class="status-badge ${event.status}">${event.status}</span></td>
                    <td>
                        <button onclick="toggleGlobalEventStatus('${event.event_id}', '${event.status}')" 
                                class="btn ${event.status === 'active' ? 'btn-danger' : 'btn-success'} btn-sm">
                            ${event.status === 'active' ? 'Disable' : 'Enable'}
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function loadGlobalStats() {
            fetch('/superadmin/api/global-stats')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error loading global stats:', data.error);
                        return;
                    }
                    updateGlobalSummaryCards(data);
                })
                .catch(error => {
                    console.error('Error loading global stats:', error);
                });
        }

        function updateGlobalSummaryCards(stats) {
            // Update the summary cards with global stats
            if (document.getElementById('global-total-operators')) {
                document.getElementById('global-total-operators').textContent = stats.total_operators || 0;
            }
            if (document.getElementById('global-total-users')) {
                document.getElementById('global-total-users').textContent = stats.total_users || 0;
            }
            if (document.getElementById('global-total-bets')) {
                document.getElementById('global-total-bets').textContent = stats.total_bets || 0;
            }
            if (document.getElementById('global-total-revenue')) {
                document.getElementById('global-total-revenue').textContent = '$' + (stats.total_revenue || 0).toFixed(2);
            }
            if (document.getElementById('global-active-events')) {
                document.getElementById('global-active-events').textContent = stats.active_events || 0;
            }
            if (document.getElementById('global-total-liability')) {
                document.getElementById('global-total-liability').textContent = '$' + (stats.total_liability || 0).toFixed(2);
            }
        }

        function loadGlobalSportsFilter(sports) {
            const select = document.getElementById('global-sport-filter');
            select.innerHTML = '<option value="">All Sports</option>';
            sports.forEach(sport => {
                const option = document.createElement('option');
                option.value = sport;
                option.textContent = sport;
                select.appendChild(option);
            });
        }

        function loadGlobalMarketsFilter(markets) {
            const select = document.getElementById('global-market-filter');
            select.innerHTML = '<option value="">All Markets</option>';
            markets.forEach(market => {
                const option = document.createElement('option');
                option.value = market;
                option.textContent = market;
                select.appendChild(option);
            });
        }

        function toggleGlobalEventStatus(eventId, currentStatus) {
            const newStatus = currentStatus === 'active' ? 'disabled' : 'active';
            
            fetch('/superadmin/api/global-betting-events/toggle-status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event_id: eventId,
                    status: newStatus
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Refresh the events to show updated status
                    loadGlobalBettingEvents();
                } else {
                    alert('Error updating event status: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to update event status');
            });
        }

        // Add event listeners for filters
        document.addEventListener('DOMContentLoaded', function() {
            // Global betting events filters
            const globalSportFilter = document.getElementById('global-sport-filter');
            const globalMarketFilter = document.getElementById('global-market-filter');
            const globalEventSearch = document.getElementById('global-event-search');
            const globalShowBetsOnly = document.getElementById('global-show-bets-only');

            if (globalSportFilter) {
                globalSportFilter.addEventListener('change', loadGlobalBettingEvents);
            }
            if (globalMarketFilter) {
                globalMarketFilter.addEventListener('change', loadGlobalBettingEvents);
            }
            if (globalEventSearch) {
                globalEventSearch.addEventListener('input', debounce(loadGlobalBettingEvents, 500));
            }
            if (globalShowBetsOnly) {
                globalShowBetsOnly.addEventListener('change', loadGlobalBettingEvents);
            }

            // Load initial global stats (since global overview is the default active tab)
            loadGlobalStats();
        });

        // Debounce function for search input
        function debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    </script>
</body>
</html>
'''

