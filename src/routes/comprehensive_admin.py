"""
Comprehensive Admin Interface - Tenant Filtered
Exact same features as admin_app.py but filtered for specific operator
"""

from flask import Blueprint, render_template_string, jsonify, request, session, redirect, url_for
import sqlite3
import json
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

comprehensive_admin_bp = Blueprint('comprehensive_admin', __name__)

DATABASE_PATH = os.getenv('DATABASE_PATH', 'src/database/app.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

def get_operator_by_subdomain(subdomain):
    """Get operator by subdomain"""
    conn = get_db_connection()
    operator = conn.execute("""
        SELECT id, sportsbook_name, subdomain, is_active, admin_username
        FROM sportsbook_operators 
        WHERE subdomain = ?
    """, (subdomain,)).fetchone()
    conn.close()
    return dict(operator) if operator else None

@comprehensive_admin_bp.route('/admin/<subdomain>/dashboard')
@admin_required
def admin_dashboard(subdomain):
    """Comprehensive admin dashboard for specific operator"""
    try:
        # Get operator info
        operator = get_operator_by_subdomain(subdomain)
        if not operator:
            return "Operator not found", 404
        
        # Verify admin belongs to this operator
        if session.get('admin_operator_id') != operator['id']:
            return "Unauthorized", 403
        
        operator_id = operator['id']
        
        # Get comprehensive admin interface HTML
        html_template = get_comprehensive_admin_template()
        
        return render_template_string(html_template, 
                                    operator=operator,
                                    operator_id=operator_id)
        
    except Exception as e:
        logger.error(f"Admin dashboard error for {subdomain}: {e}")
        return "Dashboard error", 500

@comprehensive_admin_bp.route('/api/admin/<subdomain>/betting-events')
@admin_required
def get_betting_events(subdomain):
    """Get betting events for specific operator"""
    try:
        operator = get_operator_by_subdomain(subdomain)
        if not operator or session.get('admin_operator_id') != operator['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        operator_id = operator['id']
        conn = get_db_connection()
        
        # Get events with bets from this operator's users only
        events_query = """
        SELECT DISTINCT b.match_id, b.sport_name, b.market,
               COUNT(b.id) as total_bets,
               SUM(CASE WHEN b.status = 'pending' THEN b.stake ELSE 0 END) as total_liability,
               SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as total_revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE u.sportsbook_operator_id = ?
        GROUP BY b.match_id, b.sport_name, b.market
        ORDER BY total_bets DESC
        """
        
        events = conn.execute(events_query, (operator_id,)).fetchall()
        conn.close()
        
        events_list = []
        for event in events:
            events_list.append({
                'event_id': event['match_id'],
                'sport': event['sport_name'],
                'event_name': f"{event['sport_name']} - {event['market']}",
                'market': event['market'],
                'total_bets': event['total_bets'],
                'max_liability': float(event['total_liability'] or 0),
                'max_possible_gain': float(event['total_revenue'] or 0),
                'status': 'active'
            })
        
        return jsonify({
            'success': True,
            'events': events_list,
            'total_events': len(events_list),
            'active_events': len([e for e in events_list if e['status'] == 'active'])
        })
        
    except Exception as e:
        logger.error(f"Betting events error for {subdomain}: {e}")
        return jsonify({'error': 'Failed to get events'}), 500

@comprehensive_admin_bp.route('/api/admin/<subdomain>/users')
@admin_required
def get_users(subdomain):
    """Get users for specific operator"""
    try:
        operator = get_operator_by_subdomain(subdomain)
        if not operator or session.get('admin_operator_id') != operator['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        operator_id = operator['id']
        conn = get_db_connection()
        
        # Get users for this operator only
        users_query = """
        SELECT u.id, u.username, u.email, u.balance, u.is_active, u.created_at, u.last_login,
               COUNT(b.id) as total_bets,
               COALESCE(SUM(b.stake), 0) as total_staked,
               COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return ELSE 0 END), 0) as total_payout,
               COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake 
                               WHEN b.status = 'lost' THEN -b.stake ELSE 0 END), 0) as cumulative_profit
        FROM users u
        LEFT JOIN bets b ON u.id = b.user_id
        WHERE u.sportsbook_operator_id = ?
        GROUP BY u.id, u.username, u.email, u.balance, u.is_active, u.created_at, u.last_login
        ORDER BY u.created_at DESC
        """
        
        users = conn.execute(users_query, (operator_id,)).fetchall()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'balance': float(user['balance']),
                'total_bets': user['total_bets'],
                'total_staked': float(user['total_staked']),
                'total_payout': float(user['total_payout']),
                'cumulative_profit': float(user['cumulative_profit']),
                'joined': user['created_at'][:10] if user['created_at'] else '',
                'status': 'Active' if user['is_active'] else 'Disabled',
                'is_active': user['is_active']
            })
        
        return jsonify({
            'success': True,
            'users': users_list
        })
        
    except Exception as e:
        logger.error(f"Users error for {subdomain}: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@comprehensive_admin_bp.route('/api/admin/<subdomain>/toggle-user', methods=['POST'])
@admin_required
def toggle_user_status(subdomain):
    """Enable/disable user for specific operator"""
    try:
        operator = get_operator_by_subdomain(subdomain)
        if not operator or session.get('admin_operator_id') != operator['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        conn = get_db_connection()
        
        # Verify user belongs to this operator
        user = conn.execute("""
            SELECT id, is_active FROM users 
            WHERE id = ? AND sportsbook_operator_id = ?
        """, (user_id, operator['id'])).fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Toggle user status
        new_status = not user['is_active']
        conn.execute("""
            UPDATE users SET is_active = ? WHERE id = ?
        """, (new_status, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f"User {'enabled' if new_status else 'disabled'} successfully",
            'new_status': new_status
        })
        
    except Exception as e:
        logger.error(f"Toggle user error for {subdomain}: {e}")
        return jsonify({'error': 'Failed to toggle user status'}), 500

@comprehensive_admin_bp.route('/api/admin/<subdomain>/reports')
@admin_required
def get_reports(subdomain):
    """Get comprehensive reports for specific operator"""
    try:
        operator = get_operator_by_subdomain(subdomain)
        if not operator or session.get('admin_operator_id') != operator['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        operator_id = operator['id']
        conn = get_db_connection()
        
        # Get comprehensive betting statistics for this operator
        stats_query = """
        SELECT 
            COUNT(b.id) as total_bets,
            COALESCE(SUM(b.stake), 0) as total_stakes,
            COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake 
                             WHEN b.status = 'lost' THEN -b.stake ELSE 0 END), 0) as total_revenue,
            COUNT(CASE WHEN b.status = 'pending' THEN 1 END) as pending_bets,
            COUNT(CASE WHEN b.status = 'won' THEN 1 END) as won_bets,
            COUNT(CASE WHEN b.status = 'lost' THEN 1 END) as lost_bets
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE u.sportsbook_operator_id = ?
        """
        
        stats = conn.execute(stats_query, (operator_id,)).fetchone()
        
        # Get sport performance
        sport_query = """
        SELECT b.sport_name,
               COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake 
                               WHEN b.status = 'lost' THEN -b.stake ELSE 0 END), 0) as revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        WHERE u.sportsbook_operator_id = ?
        GROUP BY b.sport_name
        ORDER BY revenue DESC
        """
        
        sports = conn.execute(sport_query, (operator_id,)).fetchall()
        
        # Get top users
        top_users_query = """
        SELECT u.username, COUNT(b.id) as bet_count
        FROM users u
        LEFT JOIN bets b ON u.id = b.user_id
        WHERE u.sportsbook_operator_id = ?
        GROUP BY u.id, u.username
        HAVING bet_count > 0
        ORDER BY bet_count DESC
        LIMIT 10
        """
        
        top_users = conn.execute(top_users_query, (operator_id,)).fetchall()
        
        conn.close()
        
        # Calculate win rate
        total_bets = stats['total_bets'] or 0
        won_bets = stats['won_bets'] or 0
        win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_bets': total_bets,
                'total_stakes': float(stats['total_stakes'] or 0),
                'total_revenue': float(stats['total_revenue'] or 0),
                'win_rate': round(win_rate, 1),
                'pending_bets': stats['pending_bets'] or 0,
                'won_bets': won_bets,
                'lost_bets': stats['lost_bets'] or 0
            },
            'sport_performance': [{'sport': s['sport_name'], 'revenue': float(s['revenue'])} for s in sports],
            'top_users': [{'username': u['username'], 'bets': u['bet_count']} for u in top_users]
        })
        
    except Exception as e:
        logger.error(f"Reports error for {subdomain}: {e}")
        return jsonify({'error': 'Failed to get reports'}), 500

def get_comprehensive_admin_template():
    """Get the comprehensive admin HTML template"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ operator.sportsbook_name }} - Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .header { background: rgba(0,0,0,0.1); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; color: white; }
        .header h1 { font-size: 1.5rem; }
        .logout-btn { background: #e74c3c; color: white; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer; }
        .container { max-width: 1400px; margin: 2rem auto; padding: 0 1rem; }
        .tabs { display: flex; gap: 1rem; margin-bottom: 2rem; }
        .tab { background: rgba(255,255,255,0.1); color: white; border: none; padding: 1rem 2rem; border-radius: 10px; cursor: pointer; transition: all 0.3s; }
        .tab.active { background: rgba(255,255,255,0.2); transform: translateY(-2px); }
        .tab-content { background: white; border-radius: 15px; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.1); display: none; }
        .tab-content.active { display: block; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem; }
        .stat-label { opacity: 0.9; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        .data-table th, .data-table td { padding: 1rem; text-align: left; border-bottom: 1px solid #eee; }
        .data-table th { background: #f8f9fa; font-weight: 600; }
        .btn { padding: 0.5rem 1rem; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9rem; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-success { background: #27ae60; color: white; }
        .btn-primary { background: #3498db; color: white; }
        .status-active { background: #27ae60; color: white; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.8rem; }
        .status-disabled { background: #e74c3c; color: white; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.8rem; }
        .loading { text-align: center; padding: 2rem; color: #666; }
        .reports-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
        .report-card { background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #667eea; }
        .report-title { font-weight: 600; margin-bottom: 1rem; color: #333; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 {{ operator.sportsbook_name }} - Admin Dashboard</h1>
        <div>
            <span>Welcome, {{ operator.admin_username }}</span>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
    </div>

    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('betting-events')">📊 Betting Events</button>
            <button class="tab" onclick="showTab('user-management')">👥 User Management</button>
            <button class="tab" onclick="showTab('reports')">📈 Reports</button>
            <button class="tab" onclick="showTab('report-builder')">🔧 Report Builder</button>
        </div>

        <!-- Betting Events Tab -->
        <div id="betting-events" class="tab-content active">
            <h2>Betting Events Management</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="total-events">-</div>
                    <div class="stat-label">Total Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="active-events">-</div>
                    <div class="stat-label">Active Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-liability">$0.00</div>
                    <div class="stat-label">Total Liability</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-revenue-events">$0.00</div>
                    <div class="stat-label">Total Revenue</div>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="refreshEvents()">🔄 Refresh Events</button>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Event ID</th>
                        <th>Sport</th>
                        <th>Event Name</th>
                        <th>Market</th>
                        <th>Total Bets</th>
                        <th>Max Liability</th>
                        <th>Revenue</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="events-table">
                    <tr><td colspan="8" class="loading">Loading events...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- User Management Tab -->
        <div id="user-management" class="tab-content">
            <h2>User Management</h2>
            <button class="btn btn-primary" onclick="refreshUsers()">🔄 Refresh Users</button>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Balance</th>
                        <th>Total Bets</th>
                        <th>Total Staked</th>
                        <th>Payout</th>
                        <th>Profit</th>
                        <th>Joined</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="users-table">
                    <tr><td colspan="11" class="loading">Loading users...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Reports Tab -->
        <div id="reports" class="tab-content">
            <h2>Reports & Analytics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="total-bets-report">-</div>
                    <div class="stat-label">Total Bets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-stakes-report">$0</div>
                    <div class="stat-label">Total Stakes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-revenue-report">$0</div>
                    <div class="stat-label">Total Revenue</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="win-rate-report">0%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="refreshReports()">🔄 Refresh Reports</button>
            
            <div class="reports-grid">
                <div class="report-card">
                    <div class="report-title">📊 Betting Overview</div>
                    <div id="betting-overview">Loading...</div>
                </div>
                <div class="report-card">
                    <div class="report-title">🏆 Sport Performance</div>
                    <div id="sport-performance">Loading...</div>
                </div>
                <div class="report-card">
                    <div class="report-title">👑 Top Users</div>
                    <div id="top-users">Loading...</div>
                </div>
            </div>
        </div>

        <!-- Report Builder Tab -->
        <div id="report-builder" class="tab-content">
            <h2>🔧 Report Builder</h2>
            <p>Generate custom reports for {{ operator.sportsbook_name }}</p>
            <div style="margin-top: 2rem;">
                <h3>📋 Available Reports</h3>
                <ul style="margin-top: 1rem; line-height: 2;">
                    <li><strong>Betting Summary:</strong> Daily betting activity by sport</li>
                    <li><strong>User Activity:</strong> User statistics and betting behavior</li>
                    <li><strong>Financial Overview:</strong> Daily revenue and financial metrics</li>
                    <li><strong>Sport Performance:</strong> Revenue and performance by sport</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        const OPERATOR_ID = {{ operator_id }};
        const SUBDOMAIN = '{{ operator.subdomain }}';
        
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load data for the tab
            if (tabName === 'betting-events') loadBettingEvents();
            if (tabName === 'user-management') loadUsers();
            if (tabName === 'reports') loadReports();
        }
        
        function loadBettingEvents() {
            fetch(`/api/admin/${SUBDOMAIN}/betting-events`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('total-events').textContent = data.total_events;
                        document.getElementById('active-events').textContent = data.active_events;
                        
                        const tbody = document.getElementById('events-table');
                        if (data.events.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #666;">No events found</td></tr>';
                        } else {
                            tbody.innerHTML = data.events.map(event => `
                                <tr>
                                    <td>${event.event_id}</td>
                                    <td>${event.sport}</td>
                                    <td>${event.event_name}</td>
                                    <td>${event.market}</td>
                                    <td>${event.total_bets}</td>
                                    <td>$${event.max_liability.toFixed(2)}</td>
                                    <td>$${event.max_possible_gain.toFixed(2)}</td>
                                    <td><span class="status-active">${event.status}</span></td>
                                </tr>
                            `).join('');
                        }
                    }
                })
                .catch(err => console.error('Error loading events:', err));
        }
        
        function loadUsers() {
            fetch(`/api/admin/${SUBDOMAIN}/users`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const tbody = document.getElementById('users-table');
                        if (data.users.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: #666;">No users found</td></tr>';
                        } else {
                            tbody.innerHTML = data.users.map(user => `
                                <tr>
                                    <td>${user.id}</td>
                                    <td>${user.username}</td>
                                    <td>${user.email}</td>
                                    <td>$${user.balance.toFixed(2)}</td>
                                    <td>${user.total_bets}</td>
                                    <td>$${user.total_staked.toFixed(2)}</td>
                                    <td>$${user.total_payout.toFixed(2)}</td>
                                    <td>$${user.cumulative_profit.toFixed(2)}</td>
                                    <td>${user.joined}</td>
                                    <td><span class="status-${user.is_active ? 'active' : 'disabled'}">${user.status}</span></td>
                                    <td>
                                        <button class="btn ${user.is_active ? 'btn-danger' : 'btn-success'}" 
                                                onclick="toggleUser(${user.id}, ${user.is_active})">
                                            ${user.is_active ? 'Disable' : 'Enable'}
                                        </button>
                                    </td>
                                </tr>
                            `).join('');
                        }
                    }
                })
                .catch(err => console.error('Error loading users:', err));
        }
        
        function loadReports() {
            fetch(`/api/admin/${SUBDOMAIN}/reports`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        document.getElementById('total-bets-report').textContent = stats.total_bets;
                        document.getElementById('total-stakes-report').textContent = `$${stats.total_stakes.toFixed(2)}`;
                        document.getElementById('total-revenue-report').textContent = `$${stats.total_revenue.toFixed(2)}`;
                        document.getElementById('win-rate-report').textContent = `${stats.win_rate}%`;
                        
                        // Betting Overview
                        document.getElementById('betting-overview').innerHTML = `
                            <div>Pending Bets: <strong>${stats.pending_bets}</strong></div>
                            <div>Won Bets: <strong>${stats.won_bets}</strong></div>
                            <div>Lost Bets: <strong>${stats.lost_bets}</strong></div>
                        `;
                        
                        // Sport Performance
                        document.getElementById('sport-performance').innerHTML = 
                            data.sport_performance.map(sport => 
                                `<div>${sport.sport}: <strong>$${sport.revenue.toFixed(2)}</strong></div>`
                            ).join('') || '<div>No data available</div>';
                        
                        // Top Users
                        document.getElementById('top-users').innerHTML = 
                            data.top_users.map(user => 
                                `<div>${user.username}: <strong>${user.bets} bets</strong></div>`
                            ).join('') || '<div>No data available</div>';
                    }
                })
                .catch(err => console.error('Error loading reports:', err));
        }
        
        function toggleUser(userId, isActive) {
            fetch(`/api/admin/${SUBDOMAIN}/toggle-user`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    loadUsers(); // Refresh the users table
                    alert(data.message);
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(err => {
                console.error('Error toggling user:', err);
                alert('Failed to toggle user status');
            });
        }
        
        function refreshEvents() { loadBettingEvents(); }
        function refreshUsers() { loadUsers(); }
        function refreshReports() { loadReports(); }
        
        function logout() {
            if (confirm('Are you sure you want to logout?')) {
                window.location.href = '/admin/logout';
            }
        }
        
        // Load initial data
        loadBettingEvents();
    </script>
</body>
</html>
    """

