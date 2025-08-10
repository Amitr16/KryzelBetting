"""
Improved Admin App for GoalServe Sports Betting Platform
Features: Proper JSON parsing, sorting, pagination, better data display
"""

from flask import Flask, render_template_string, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Database path (using the existing GoalServe database)
DATABASE_PATH = 'src/database/app.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_event_financials(event_id, sport_name):
    """Calculate max liability and max possible gain for a betting event"""
    try:
        conn = get_db_connection()
        
        # Get all pending bets for this event
        query = """
        SELECT bet_selection, stake, potential_return, odds
        FROM bets 
        WHERE match_id = ? AND sport_name = ? AND status = 'pending'
        """
        
        bets = conn.execute(query, (event_id, sport_name)).fetchall()
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

@app.route('/')
def admin_dashboard():
    """Main admin dashboard"""
    return render_template_string(ADMIN_TEMPLATE)

@app.route('/api/betting-events')
def get_betting_events():
    """Get all available betting events from JSON files with improved parsing"""
    try:
        import os
        import json
        
        # Get database connection for checking disabled events
        conn = get_db_connection()
        
        # Path to Sports Pre Match directory
        sports_dir = 'Sports Pre Match'
        
        all_events = []
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get filter and search parameters
        sport_filter = request.args.get('sport', '')  # Show all sports by default
        market_filter = request.args.get('market', '')
        search_query = request.args.get('search', '').lower()
        sort_by = request.args.get('sort_by', 'event_id')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Optimize: Only process the specific sport if filter is applied
        sports_to_process = []
        if sport_filter:
            # Only process the filtered sport
            sports_to_process = [sport_filter]
        else:
            # Process all sports (slower)
            sports_to_process = [sport_name for sport_name in os.listdir(sports_dir) 
                               if os.path.isdir(os.path.join(sports_dir, sport_name))]
        
        # Remove market_filter from backend processing - will be handled in frontend
        market_filter = None
        
        for sport_name in sports_to_process:
            sport_path = os.path.join(sports_dir, sport_name)
            if not os.path.isdir(sport_path):
                continue
                
            # Look for JSON file
            json_path = os.path.join(sport_path, f"{sport_name}_odds.json")
            if not os.path.exists(json_path):
                continue
                
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Extract sport display name from metadata
                sport_display_name = sport_name.title()
                if 'metadata' in data and 'display_name' in data['metadata']:
                    sport_display_name = data['metadata']['display_name']
                
                # Navigate to matches
                if 'odds_data' in data and 'scores' in data['odds_data']:
                    scores = data['odds_data']['scores']
                    if 'categories' in scores:
                        for category in scores['categories']:
                            if 'matches' in category:
                                category_name = category.get('name', 'Unknown Category')
                                
                                for match in category['matches']:
                                    event_id = match.get('id', '')
                                    
                                    # Extract team names properly
                                    localteam = match.get('localteam', {})
                                    visitorteam = match.get('visitorteam', {})
                                    
                                    # Handle different sport structures
                                    if sport_name == 'tennis':
                                        # Tennis uses player_1 and player_2
                                        home_team = match.get('player_1', {}).get('name', 'Unknown')
                                        away_team = match.get('player_2', {}).get('name', 'Unknown')
                                    else:
                                        # Other sports use localteam and visitorteam
                                        home_team = localteam.get('name', 'Unknown') if isinstance(localteam, dict) else str(localteam)
                                        away_team = visitorteam.get('name', 'Unknown') if isinstance(visitorteam, dict) else str(visitorteam)
                                    
                                    # Debug: Print team names for troubleshooting
                                    if home_team == 'Unknown' or away_team == 'Unknown':
                                        print(f"Debug - Sport: {sport_name}, Match ID: {event_id}")
                                        print(f"  Localteam: {localteam}")
                                        print(f"  Visitorteam: {visitorteam}")
                                        print(f"  Home: {home_team}, Away: {away_team}")
                                    
                                    event_name = f"{home_team} vs {away_team}"
                                    
                                    # Skip if search query doesn't match
                                    if search_query and search_query not in event_name.lower():
                                        continue
                                    
                                    # Process odds/markets
                                    if 'odds' in match:
                                        for odds_entry in match['odds']:
                                            market_id = odds_entry.get('id', 'unknown')
                                            market_name = odds_entry.get('value', 'Unknown Market')
                                            market_key = f"market_{market_id}"  # Use the unique ID instead of name
                                            
                                            # Market filtering moved to frontend - no backend filtering
                                                
                                            # Create unique ID for this specific market within the event
                                            unique_market_id = f"{event_id}_{market_key}"
                                            
                                            # Create betting event entry
                                            betting_event = {
                                                'id': unique_market_id,
                                                'unique_id': unique_market_id,  # Explicit unique identifier
                                                'event_id': event_id,
                                                'sport': sport_display_name,
                                                'event_name': event_name,
                                                'market': market_name,
                                                'market_display': market_name,
                                                'category': category_name,
                                                'odds_data': odds_entry,
                                                'is_active': True,  # Will be updated below
                                                'date': match.get('date', ''),
                                                'time': match.get('time', ''),
                                                'status': match.get('status', 'Unknown')
                                            }
                                            
                                            # Check if this event is disabled
                                            event_key = f"{event_id}_{market_key}"
                                            disabled_check = conn.execute(
                                                'SELECT * FROM disabled_events WHERE event_key = ?', 
                                                (event_key,)
                                            ).fetchone()
                                            betting_event['is_active'] = disabled_check is None
                                            
                                            # Calculate financial metrics for this specific market
                                            # Only calculate if there are actual bets on this market
                                            market_bets = conn.execute("""
                                                SELECT COUNT(*) as bet_count, SUM(stake) as total_stake
                                                FROM bets 
                                                WHERE match_id = ? AND sport_name = ? AND status = 'pending'
                                            """, (event_id, sport_name)).fetchone()
                                            
                                            # Calculate financials for this specific market only
                                            market_specific_bets = conn.execute("""
                                                SELECT bet_selection, stake, potential_return, odds
                                                FROM bets 
                                                WHERE match_id = ? AND sport_name = ? AND market = ? AND status = 'pending'
                                            """, (event_id, sport_name, market_id)).fetchall()
                                            
                                            if market_specific_bets:
                                                # Calculate financials for this specific market only
                                                selections = {}
                                                total_stakes = 0
                                                
                                                for bet in market_specific_bets:
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
                                                
                                                betting_event['max_liability'] = max_liability
                                                betting_event['max_possible_gain'] = max_possible_gain
                                            else:
                                                # No bets on this specific market - show $0.00
                                                betting_event['max_liability'] = 0.0
                                                betting_event['max_possible_gain'] = 0.0
                                            
                                            all_events.append(betting_event)
                                        
            except Exception as e:
                print(f"Error reading {json_path}: {e}")
                continue
        
        # Sort events
        reverse = sort_order == 'desc'
        if sort_by == 'event_id':
            all_events.sort(key=lambda x: int(x['event_id']) if x['event_id'].isdigit() else 0, reverse=reverse)
        elif sort_by == 'sport':
            all_events.sort(key=lambda x: x['sport'], reverse=reverse)
        elif sort_by == 'event_name':
            all_events.sort(key=lambda x: x['event_name'], reverse=reverse)
        elif sort_by == 'market':
            all_events.sort(key=lambda x: x['market'], reverse=reverse)
        elif sort_by == 'max_liability':
            all_events.sort(key=lambda x: x['max_liability'], reverse=reverse)
        elif sort_by == 'max_possible_gain':
            all_events.sort(key=lambda x: x['max_possible_gain'], reverse=reverse)
        elif sort_by == 'status':
            all_events.sort(key=lambda x: x['is_active'], reverse=reverse)
        
        # Apply pagination
        total_events = len(all_events)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_events = all_events[start_idx:end_idx]
        
        # Get unique sports and markets for filters
        # For sports, get ALL available sports regardless of filtering
        all_sports = []
        for sport_name in os.listdir(sports_dir):
            sport_path = os.path.join(sports_dir, sport_name)
            if os.path.isdir(sport_path):
                json_path = os.path.join(sport_path, f"{sport_name}_odds.json")
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        sport_display_name = sport_name.title()
                        if 'metadata' in data and 'display_name' in data['metadata']:
                            sport_display_name = data['metadata']['display_name']
                        all_sports.append(sport_display_name)
                    except:
                        all_sports.append(sport_name.title())
        
        # For markets, use the filtered results
        unique_markets = list(set(event['market'] for event in all_events))
        
        # Calculate summary statistics
        active_events = len([e for e in all_events if e['is_active']])
        total_liability = sum(e['max_liability'] for e in all_events)
        total_gain = sum(e['max_possible_gain'] for e in all_events)
        
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
                'total_events': total_events,
                'active_events': active_events,
                'total_liability': total_liability,
                'total_gain': total_gain,
                'unique_sports': len(all_sports),
                'unique_markets': len(unique_markets)
            },
            'filters': {
                'sports': sorted(all_sports),
                'markets': sorted(unique_markets)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/betting-events/<event_key>/toggle', methods=['POST'])
def toggle_event_status(event_key):
    """Toggle event active status"""
    try:
        conn = get_db_connection()
        
        # Check if event is currently disabled
        disabled_event = conn.execute(
            'SELECT * FROM disabled_events WHERE event_key = ?', 
            (event_key,)
        ).fetchone()
        
        if disabled_event:
            # Event is disabled, enable it by removing from disabled_events
            conn.execute('DELETE FROM disabled_events WHERE event_key = ?', (event_key,))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Event enabled successfully',
                'is_active': True
            })
        else:
            # Event is active, disable it by adding to disabled_events
            # Parse event_key to extract components (format: event_id_market)
            parts = event_key.split('_')
            if len(parts) >= 2:
                event_id = '_'.join(parts[:-1])
                market = parts[-1]
            else:
                event_id = event_key
                market = 'unknown'
            
            conn.execute(
                'INSERT OR REPLACE INTO disabled_events (event_key, sport, event_name, market) VALUES (?, ?, ?, ?)',
                (event_key, 'unknown', 'Unknown Event', market)
            )
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Event disabled successfully',
                'is_active': False
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users')
def get_users():
    """Get all users with betting statistics"""
    try:
        conn = get_db_connection()
        
        # Get users with betting stats
        query = """
        SELECT 
            u.id,
            u.username,
            u.email,
            u.balance,
            u.created_at,
            u.is_active,
            COUNT(b.id) as total_bets,
            COALESCE(SUM(b.stake), 0) as total_staked,
            COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END), 0) as cumulative_profit
        FROM users u
        LEFT JOIN bets b ON u.id = b.user_id
        GROUP BY u.id, u.username, u.email, u.balance, u.created_at, u.is_active
        ORDER BY u.created_at DESC
        """
        
        users = conn.execute(query).fetchall()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'balance': f"${user['balance']:.2f}",
                'total_bets': user['total_bets'],
                'total_staked': f"${user['total_staked']:.2f}",
                'cumulative_profit': f"${user['cumulative_profit']:.2f}",
                'joined': user['created_at'][:10] if user['created_at'] else 'Unknown',
                'is_active': user['is_active']
            })
        
        return jsonify({'users': users_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/toggle', methods=['POST'])
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        conn = get_db_connection()
        
        # Get current user status
        user = conn.execute('SELECT is_active FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Toggle status
        new_status = not user['is_active']
        conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'User {"enabled" if new_status else "disabled"} successfully',
            'is_active': new_status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# HTML Template with improved UI, sorting, and pagination
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GoalServe Admin Dashboard</title>
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
            gap: 1rem;
        }
        
        .header h1 {
            font-size: 1.5rem;
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
            position: relative;
        }
        
        th:hover {
            background: #e9ecef;
        }
        
        th.sortable::after {
            content: ' ↕';
            opacity: 0.5;
        }
        
        th.sort-asc::after {
            content: ' ↑';
            opacity: 1;
        }
        
        th.sort-desc::after {
            content: ' ↓';
            opacity: 1;
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
        
        .liability {
            color: #dc3545;
            font-weight: 600;
        }
        
        .gain {
            color: #28a745;
            font-weight: 600;
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
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .pagination button {
            padding: 0.5rem 1rem;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 4px;
        }
        
        .pagination button:hover:not(:disabled) {
            background: #f8f9fa;
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .pagination .current-page {
            font-weight: 600;
            color: #667eea;
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
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 GoalServe Admin Dashboard</h1>
    </div>
    
    <div class="container">
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showSection('betting-events')">📊 Betting Events</button>
            <button class="nav-tab" onclick="showSection('user-management')">👥 User Management</button>
        </div>
        
        <!-- Betting Events Section -->
        <div id="betting-events" class="content-section active">
            <h2>Betting Events Management</h2>
            
            <div class="summary-cards">
                <div class="summary-card">
                    <h3>Total Events</h3>
                    <div class="value" id="total-events">-</div>
                </div>
                <div class="summary-card">
                    <h3>Active Events</h3>
                    <div class="value" id="active-events">-</div>
                </div>
                <div class="summary-card">
                    <h3>Max Liability</h3>
                    <div class="value" id="max-liability">$0.00</div>
                </div>
                <div class="summary-card">
                    <h3>Max Possible Gain</h3>
                    <div class="value" id="max-possible-gain">$0.00</div>
                </div>
            </div>
            
            <div class="controls">
                <select id="sport-filter">
                    <option value="">All Sports</option>
                </select>
                <select id="market-filter">
                    <option value="">All Markets</option>
                </select>
                <input type="text" id="search-input" placeholder="Search event names...">
                <select id="per-page-select">
                    <option value="10">10 per page</option>
                    <option value="20" selected>20 per page</option>
                    <option value="50">50 per page</option>
                    <option value="100">100 per page</option>
                </select>
                <button onclick="loadBettingEvents()">🔄 Refresh Events</button>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="unique_id">Unique ID</th>
                            <th class="sortable" data-sort="sport">Sport</th>
                            <th class="sortable" data-sort="event_name">Event Name</th>
                            <th class="sortable" data-sort="market">Market</th>
                            <th class="sortable" data-sort="max_liability">Max Liability</th>
                            <th class="sortable" data-sort="max_possible_gain">Max Possible Gain</th>
                            <th class="sortable" data-sort="status">Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="events-table-body">
                        <tr><td colspan="8" class="loading">Loading events...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div class="pagination" id="events-pagination">
                <!-- Pagination will be inserted here -->
            </div>
        </div>
        
        <!-- User Management Section -->
        <div id="user-management" class="content-section">
            <h2>User Management</h2>
            
            <div class="controls">
                <button onclick="loadUsers()">🔄 Refresh Users</button>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Balance</th>
                            <th>Total Bets</th>
                            <th>Total Staked</th>
                            <th>Cumulative Profit</th>
                            <th>Joined</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="users-table-body">
                        <tr><td colspan="10" class="loading">Loading users...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let currentPage = 1;
        let currentSort = 'event_id';
        let currentSortOrder = 'asc';
        let allEvents = []; // Store all events for client-side filtering
        
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
            
            // Load data for the section
            if (sectionId === 'betting-events') {
                loadBettingEvents();
            } else if (sectionId === 'user-management') {
                loadUsers();
            }
        }
        
        function loadBettingEvents(page = 1) {
            currentPage = page;
            
            const sportFilter = document.getElementById('sport-filter').value;
            const marketFilter = document.getElementById('market-filter').value;
            const searchQuery = document.getElementById('search-input').value;
            const perPage = document.getElementById('per-page-select').value;
            
            const params = new URLSearchParams({
                page: page,
                per_page: perPage,
                sort_by: currentSort,
                sort_order: currentSortOrder
            });
            
            if (sportFilter) params.append('sport', sportFilter);
            if (searchQuery) params.append('search', searchQuery);
            // Market filter removed from backend - will be handled in frontend
            
            fetch(`/api/betting-events?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('events-table-body').innerHTML = 
                            `<tr><td colspan="8" class="error">Error: ${data.error}</td></tr>`;
                        return;
                    }
                    
                    // Update summary cards
                    document.getElementById('total-events').textContent = data.summary.total_events;
                    document.getElementById('active-events').textContent = data.summary.active_events;
                    document.getElementById('max-liability').textContent = `$${data.summary.total_liability.toFixed(2)}`;
                    document.getElementById('max-possible-gain').textContent = `$${data.summary.total_gain.toFixed(2)}`;
                    
                    // Store all events for client-side filtering
                    allEvents = data.events;
                    
                    // Update filters
                    updateFilters(data.filters);
                    
                    // Update table with client-side filtering
                    updateEventsTableWithFiltering();
                    
                    // Update pagination
                    updatePagination(data.pagination, 'events');
                })
                .catch(error => {
                    console.error('Error loading events:', error);
                    document.getElementById('events-table-body').innerHTML = 
                        `<tr><td colspan="8" class="error">Failed to load events</td></tr>`;
                });
        }
        
        function updateFilters(filters) {
            const sportFilter = document.getElementById('sport-filter');
            const marketFilter = document.getElementById('market-filter');
            
            // Update sport filter
            const currentSport = sportFilter.value;
            sportFilter.innerHTML = '<option value="">All Sports</option>';
            filters.sports.forEach(sport => {
                const option = document.createElement('option');
                option.value = sport.toLowerCase();
                option.textContent = sport;
                if (sport.toLowerCase() === currentSport) option.selected = true;
                sportFilter.appendChild(option);
            });
            
            // Update market filter
            const currentMarket = marketFilter.value;
            marketFilter.innerHTML = '<option value="">All Markets</option>';
            filters.markets.forEach(market => {
                const option = document.createElement('option');
                option.value = market.toLowerCase();
                option.textContent = market;
                if (market.toLowerCase() === currentMarket) option.selected = true;
                marketFilter.appendChild(option);
            });
        }
        
        function updateEventsTableWithFiltering() {
            const marketFilter = document.getElementById('market-filter').value.toLowerCase();
            
            // Filter events by market on client-side
            let filteredEvents = allEvents;
            if (marketFilter) {
                filteredEvents = allEvents.filter(event => 
                    event.market.toLowerCase().includes(marketFilter)
                );
            }
            
            const tbody = document.getElementById('events-table-body');
            
            if (filteredEvents.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="loading">No events found</td></tr>';
                return;
            }
            
            tbody.innerHTML = filteredEvents.map(event => `
                <tr>
                    <td>${event.unique_id}</td>
                    <td>${event.sport}</td>
                    <td>${event.event_name}</td>
                    <td>${event.market}</td>
                    <td class="liability">$${event.max_liability.toFixed(2)}</td>
                    <td class="gain">$${event.max_possible_gain.toFixed(2)}</td>
                    <td>
                        <span class="status-badge ${event.is_active ? 'status-active' : 'status-disabled'}">
                            ${event.is_active ? 'Active' : 'Disabled'}
                        </span>
                    </td>
                    <td>
                        <button class="action-btn ${event.is_active ? 'btn-disable' : 'btn-enable'}" 
                                onclick="toggleEvent('${event.unique_id}')">
                            ${event.is_active ? 'Disable' : 'Enable'}
                        </button>
                    </td>
                </tr>
            `).join('');
        }
        
        function updateEventsTable(events) {
            const tbody = document.getElementById('events-table-body');
            
            if (events.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="loading">No events found</td></tr>';
                return;
            }
            
            tbody.innerHTML = events.map(event => `
                <tr>
                    <td>${event.event_id}</td>
                    <td>${event.sport}</td>
                    <td>${event.event_name}</td>
                    <td>${event.market}</td>
                    <td class="liability">$${event.max_liability.toFixed(2)}</td>
                    <td class="gain">$${event.max_possible_gain.toFixed(2)}</td>
                    <td>
                        <span class="status-badge ${event.is_active ? 'status-active' : 'status-disabled'}">
                            ${event.is_active ? 'Active' : 'Disabled'}
                        </span>
                    </td>
                    <td>
                        <button class="action-btn ${event.is_active ? 'btn-disable' : 'btn-enable'}" 
                                onclick="toggleEvent('${event.id}')">
                            ${event.is_active ? 'Disable' : 'Enable'}
                        </button>
                    </td>
                </tr>
            `).join('');
        }
        
        function updatePagination(pagination, type) {
            const container = document.getElementById(`${type}-pagination`);
            
            const prevDisabled = pagination.page <= 1 ? 'disabled' : '';
            const nextDisabled = pagination.page >= pagination.pages ? 'disabled' : '';
            
            container.innerHTML = `
                <button ${prevDisabled} onclick="loadBettingEvents(${pagination.page - 1})">Previous</button>
                <span class="current-page">Page ${pagination.page} of ${pagination.pages}</span>
                <span>(${pagination.total} total events)</span>
                <button ${nextDisabled} onclick="loadBettingEvents(${pagination.page + 1})">Next</button>
            `;
        }
        
        function toggleEvent(eventId) {
            fetch(`/api/betting-events/${eventId}/toggle`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadBettingEvents(currentPage);
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error toggling event:', error);
                alert('Failed to toggle event status');
            });
        }
        
        function loadUsers() {
            fetch('/api/users')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('users-table-body').innerHTML = 
                            `<tr><td colspan="10" class="error">Error: ${data.error}</td></tr>`;
                        return;
                    }
                    
                    updateUsersTable(data.users);
                })
                .catch(error => {
                    console.error('Error loading users:', error);
                    document.getElementById('users-table-body').innerHTML = 
                        `<tr><td colspan="10" class="error">Failed to load users</td></tr>`;
                });
        }
        
        function updateUsersTable(users) {
            const tbody = document.getElementById('users-table-body');
            
            if (users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" class="loading">No users found</td></tr>';
                return;
            }
            
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.email}</td>
                    <td>${user.balance}</td>
                    <td>${user.total_bets}</td>
                    <td>${user.total_staked}</td>
                    <td class="${user.cumulative_profit.startsWith('-') ? 'liability' : 'gain'}">${user.cumulative_profit}</td>
                    <td>${user.joined}</td>
                    <td>
                        <span class="status-badge ${user.is_active ? 'status-active' : 'status-disabled'}">
                            ${user.is_active ? 'Active' : 'Disabled'}
                        </span>
                    </td>
                    <td>
                        <button class="action-btn ${user.is_active ? 'btn-disable' : 'btn-enable'}" 
                                onclick="toggleUser(${user.id})">
                            ${user.is_active ? 'Disable' : 'Enable'}
                        </button>
                    </td>
                </tr>
            `).join('');
        }
        
        function toggleUser(userId) {
            fetch(`/api/users/${userId}/toggle`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadUsers();
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error toggling user:', error);
                alert('Failed to toggle user status');
            });
        }
        
        // Add sorting functionality
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('th.sortable').forEach(th => {
                th.addEventListener('click', function() {
                    const sortBy = this.dataset.sort;
                    
                    if (currentSort === sortBy) {
                        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
                    } else {
                        currentSort = sortBy;
                        currentSortOrder = 'asc';
                    }
                    
                    // Update visual indicators
                    document.querySelectorAll('th.sortable').forEach(header => {
                        header.classList.remove('sort-asc', 'sort-desc');
                    });
                    
                    this.classList.add(currentSortOrder === 'asc' ? 'sort-asc' : 'sort-desc');
                    
                    loadBettingEvents(1);
                });
            });
            
            // Add event listeners for filters
            document.getElementById('sport-filter').addEventListener('change', () => loadBettingEvents(1));
            document.getElementById('market-filter').addEventListener('change', () => updateEventsTableWithFiltering());
            document.getElementById('search-input').addEventListener('input', () => loadBettingEvents(1));
            document.getElementById('per-page-select').addEventListener('change', () => loadBettingEvents(1));
            
            // Load initial data
            loadBettingEvents();
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

