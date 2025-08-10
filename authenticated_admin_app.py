"""
Authenticated Admin App for GoalServe Sports Betting Platform
Features: Authentication, Tenant-specific data filtering, User Management, Reports
"""

from flask import Flask, render_template_string, jsonify, request, send_file, make_response, session, redirect, url_for
import sqlite3
import json
from datetime import datetime, timedelta
import os
import io
import csv
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Database path
DATABASE_PATH = 'src/database/app.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'operator_id' not in session:
            # If it's an API request, return JSON error
            if request.path.startswith('/api/') or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401
            # Otherwise redirect to login
            return redirect('/admin-login.html')
        return f(*args, **kwargs)
    return decorated_function

def get_current_operator():
    """Get current operator info from session"""
    if 'operator_id' not in session:
        return None
    
    conn = get_db_connection()
    operator = conn.execute("""
        SELECT id, login, sportsbook_name, subdomain, email, is_active, total_revenue, commission_rate
        FROM sportsbook_operators 
        WHERE id = ?
    """, (session['operator_id'],)).fetchone()
    conn.close()
    
    return dict(operator) if operator else None

def calculate_event_financials(event_id, market_id, sport_name, operator_id):
    """Calculate max liability and max possible gain for a specific event+market combination (tenant-filtered)"""
    try:
        conn = get_db_connection()
        
        # Get all pending bets for this specific event+market combination and operator
        query = """
        SELECT bet_selection, stake, potential_return, odds
        FROM bets 
        WHERE match_id = ? AND market = ? AND sport_name = ? AND status = 'pending' AND sportsbook_operator_id = ?
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
            stake = bet['stake']
            potential_return = bet['potential_return']
            
            total_stakes += stake
            
            if selection not in selections:
                selections[selection] = {
                    'total_stake': 0,
                    'total_potential_return': 0,
                    'bet_count': 0
                }
            
            selections[selection]['total_stake'] += stake
            selections[selection]['total_potential_return'] += potential_return
            selections[selection]['bet_count'] += 1
        
        if not selections:
            return 0.0, 0.0
        
        # Calculate max liability (worst case scenario for the house)
        max_liability = 0
        max_gain = total_stakes  # Best case: all bets lose, house keeps all stakes
        
        for selection, data in selections.items():
            # If this selection wins, house pays out potential returns but keeps other stakes
            other_stakes = total_stakes - data['total_stake']
            liability = data['total_potential_return'] - other_stakes
            
            if liability > max_liability:
                max_liability = liability
        
        return max(0, max_liability), max_gain
        
    except Exception as e:
        print(f"Error calculating financials: {e}")
        return 0.0, 0.0

@app.route('/admin/<subdomain>')
@app.route('/admin/<subdomain>/')
def admin_redirect(subdomain):
    """Redirect to admin dashboard"""
    return redirect(f'/admin/{subdomain}/dashboard')

@app.route('/admin/<subdomain>/dashboard')
@require_admin_auth
def admin_dashboard(subdomain):
    """Main admin dashboard"""
    operator = get_current_operator()
    if not operator or operator['subdomain'] != subdomain:
        return redirect('/admin-login.html')
    
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE, operator=operator)

@app.route('/api/admin/stats')
@require_admin_auth
def get_admin_stats():
    """Get admin statistics (tenant-filtered)"""
    try:
        operator_id = session['operator_id']
        conn = get_db_connection()
        
        # Get user count
        user_count = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE sportsbook_operator_id = ?", 
            (operator_id,)
        ).fetchone()['count']
        
        # Get total bets
        total_bets = conn.execute(
            "SELECT COUNT(*) as count FROM bets WHERE sportsbook_operator_id = ?", 
            (operator_id,)
        ).fetchone()['count']
        
        # Get pending bets
        pending_bets = conn.execute(
            "SELECT COUNT(*) as count FROM bets WHERE status = 'pending' AND sportsbook_operator_id = ?", 
            (operator_id,)
        ).fetchone()['count']
        
        # Get total revenue (sum of stakes from lost bets minus payouts from won bets)
        revenue_data = conn.execute("""
            SELECT 
                SUM(CASE WHEN status = 'lost' THEN stake ELSE 0 END) as total_stakes_lost,
                SUM(CASE WHEN status = 'won' THEN actual_return ELSE 0 END) as total_payouts
            FROM bets 
            WHERE sportsbook_operator_id = ?
        """, (operator_id,)).fetchone()
        
        total_stakes_lost = revenue_data['total_stakes_lost'] or 0
        total_payouts = revenue_data['total_payouts'] or 0
        total_revenue = total_stakes_lost - total_payouts
        
        # Get today's stats
        today = datetime.now().strftime('%Y-%m-%d')
        today_bets = conn.execute("""
            SELECT COUNT(*) as count 
            FROM bets 
            WHERE DATE(created_at) = ? AND sportsbook_operator_id = ?
        """, (today, operator_id)).fetchone()['count']
        
        today_revenue = conn.execute("""
            SELECT 
                SUM(CASE WHEN status = 'lost' THEN stake ELSE 0 END) as stakes_lost,
                SUM(CASE WHEN status = 'won' THEN actual_return ELSE 0 END) as payouts
            FROM bets 
            WHERE DATE(created_at) = ? AND sportsbook_operator_id = ?
        """, (today, operator_id)).fetchone()
        
        today_stakes_lost = today_revenue['stakes_lost'] or 0
        today_payouts = today_revenue['payouts'] or 0
        today_net_revenue = today_stakes_lost - today_payouts
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'user_count': user_count,
                'total_bets': total_bets,
                'pending_bets': pending_bets,
                'total_revenue': round(total_revenue, 2),
                'today_bets': today_bets,
                'today_revenue': round(today_net_revenue, 2)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/users')
@require_admin_auth
def get_users():
    """Get users list (tenant-filtered)"""
    try:
        operator_id = session['operator_id']
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '').strip()
        
        conn = get_db_connection()
        
        # Build query with search
        base_query = "FROM users WHERE sportsbook_operator_id = ?"
        params = [operator_id]
        
        if search:
            base_query += " AND (username LIKE ? OR email LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        # Get total count
        total_count = conn.execute(f"SELECT COUNT(*) as count {base_query}", params).fetchone()['count']
        
        # Get paginated results
        offset = (page - 1) * per_page
        users = conn.execute(f"""
            SELECT id, username, email, balance, created_at, last_login, is_active
            {base_query}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': [dict(user) for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/bets')
@require_admin_auth
def get_bets():
    """Get bets list (tenant-filtered)"""
    try:
        operator_id = session['operator_id']
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', '').strip()
        
        conn = get_db_connection()
        
        # Build query with filters
        base_query = """
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE b.sportsbook_operator_id = ?
        """
        params = [operator_id]
        
        if status:
            base_query += " AND b.status = ?"
            params.append(status)
        
        # Get total count
        total_count = conn.execute(f"SELECT COUNT(*) as count {base_query}", params).fetchone()['count']
        
        # Get paginated results
        offset = (page - 1) * per_page
        bets = conn.execute(f"""
            SELECT 
                b.id, b.match_name, b.selection, b.stake, b.odds, 
                b.potential_return, b.status, b.created_at, b.settled_at,
                u.username
            {base_query}
            ORDER BY b.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'bets': [dict(bet) for bet in bets],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Logout admin"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

# Admin Dashboard HTML Template
ADMIN_DASHBOARD_TEMPLATE = """
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #334155;
        }

        .header {
            background: white;
            border-bottom: 1px solid #e2e8f0;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.25rem;
            font-weight: bold;
            color: #1e293b;
        }

        .logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #4ade80, #22c55e);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .logout-btn {
            background: #ef4444;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }

        .logout-btn:hover {
            background: #dc2626;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .page-title {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #1e293b;
        }

        .page-subtitle {
            color: #64748b;
            margin-bottom: 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }

        .stat-title {
            font-size: 0.875rem;
            font-weight: 500;
            color: #64748b;
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1e293b;
        }

        .stat-change {
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }

        .stat-change.positive {
            color: #059669;
        }

        .stat-change.negative {
            color: #dc2626;
        }

        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }

        .section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #1e293b;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
        }

        .table th,
        .table td {
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
        }

        .table th {
            font-weight: 600;
            color: #374151;
            background: #f8fafc;
        }

        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }

        .status-pending {
            background: #fef3c7;
            color: #92400e;
        }

        .status-won {
            background: #d1fae5;
            color: #065f46;
        }

        .status-lost {
            background: #fee2e2;
            color: #991b1b;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #64748b;
        }

        @media (max-width: 768px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon">⚽</div>
            <span>{{ operator.sportsbook_name }}</span>
        </div>
        <div class="user-info">
            <span>Welcome, {{ operator.login }}</span>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
    </div>

    <div class="container">
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Overview of your sportsbook operations</p>

        <div class="stats-grid" id="statsGrid">
            <div class="loading">Loading statistics...</div>
        </div>

        <div class="content-grid">
            <div class="section">
                <h2 class="section-title">Recent Users</h2>
                <div id="recentUsers" class="loading">Loading users...</div>
            </div>

            <div class="section">
                <h2 class="section-title">Recent Bets</h2>
                <div id="recentBets" class="loading">Loading bets...</div>
            </div>
        </div>
    </div>

    <script>
        // Load dashboard data
        async function loadDashboard() {
            try {
                // Load stats
                const statsResponse = await fetch('/api/admin/stats');
                const statsData = await statsResponse.json();
                
                if (statsData.success) {
                    displayStats(statsData.stats);
                }

                // Load recent users
                const usersResponse = await fetch('/api/admin/users?per_page=5');
                const usersData = await usersResponse.json();
                
                if (usersData.success) {
                    displayRecentUsers(usersData.users);
                }

                // Load recent bets
                const betsResponse = await fetch('/api/admin/bets?per_page=5');
                const betsData = await betsResponse.json();
                
                if (betsData.success) {
                    displayRecentBets(betsData.bets);
                }

            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }

        function displayStats(stats) {
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-title">Total Users</div>
                    <div class="stat-value">${stats.user_count}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Total Bets</div>
                    <div class="stat-value">${stats.total_bets}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Pending Bets</div>
                    <div class="stat-value">${stats.pending_bets}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Total Revenue</div>
                    <div class="stat-value">$${stats.total_revenue}</div>
                    <div class="stat-change">Today: $${stats.today_revenue}</div>
                </div>
            `;
        }

        function displayRecentUsers(users) {
            const container = document.getElementById('recentUsers');
            
            if (users.length === 0) {
                container.innerHTML = '<p>No users yet</p>';
                return;
            }

            const table = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Balance</th>
                            <th>Joined</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                            <tr>
                                <td>${user.username}</td>
                                <td>$${user.balance}</td>
                                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            
            container.innerHTML = table;
        }

        function displayRecentBets(bets) {
            const container = document.getElementById('recentBets');
            
            if (bets.length === 0) {
                container.innerHTML = '<p>No bets yet</p>';
                return;
            }

            const table = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Stake</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bets.map(bet => `
                            <tr>
                                <td>${bet.username}</td>
                                <td>$${bet.stake}</td>
                                <td><span class="status-badge status-${bet.status}">${bet.status}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            
            container.innerHTML = table;
        }

        async function logout() {
            try {
                await fetch('/api/admin/logout', { method: 'POST' });
                window.location.href = '/admin-login.html';
            } catch (error) {
                console.error('Logout error:', error);
                window.location.href = '/admin-login.html';
            }
        }

        // Load dashboard on page load
        loadDashboard();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

