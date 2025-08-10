"""
Comprehensive Super Admin Interface - Global Level
Same features as admin but across ALL operators + additional super admin features
"""

from flask import Blueprint, render_template_string, jsonify, request, session, redirect
import sqlite3
import json
from datetime import datetime, timedelta
from functools import wraps
import logging
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

comprehensive_superadmin_bp = Blueprint('comprehensive_superadmin', __name__)

DATABASE_PATH = 'src/database/app.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def superadmin_required(f):
    """Decorator to require super admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'superadmin_id' not in session:
            return redirect('/superadmin')
        return f(*args, **kwargs)
    return decorated_function

@comprehensive_superadmin_bp.route('/superadmin/comprehensive-dashboard')
@superadmin_required
def superadmin_comprehensive_dashboard():
    """Comprehensive super admin dashboard"""
    try:
        html_template = get_comprehensive_superadmin_template()
        return render_template_string(html_template)
        
    except Exception as e:
        logger.error(f"Super admin comprehensive dashboard error: {e}")
        return "Dashboard error", 500

@comprehensive_superadmin_bp.route('/api/superadmin/global-betting-events')
@superadmin_required
def get_global_betting_events():
    """Get betting events across ALL operators"""
    try:
        conn = get_db_connection()
        
        # Get events with bets from ALL operators
        events_query = """
        SELECT DISTINCT b.match_id, b.sport_name, b.market, so.sportsbook_name,
               COUNT(b.id) as total_bets,
               SUM(CASE WHEN b.status = 'pending' THEN b.stake ELSE 0 END) as total_liability,
               SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake ELSE 0 END) as total_revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        JOIN sportsbook_operators so ON u.sportsbook_operator_id = so.id
        GROUP BY b.match_id, b.sport_name, b.market, so.sportsbook_name
        ORDER BY total_bets DESC
        """
        
        events = conn.execute(events_query).fetchall()
        conn.close()
        
        events_list = []
        for event in events:
            events_list.append({
                'event_id': event['match_id'],
                'sport': event['sport_name'],
                'event_name': f"{event['sport_name']} - {event['market']}",
                'market': event['market'],
                'operator': event['sportsbook_name'],
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
        logger.error(f"Global betting events error: {e}")
        return jsonify({'error': 'Failed to get events'}), 500

@comprehensive_superadmin_bp.route('/api/superadmin/global-users')
@superadmin_required
def get_global_users():
    """Get users across ALL operators"""
    try:
        conn = get_db_connection()
        
        # Get users from ALL operators
        users_query = """
        SELECT u.id, u.username, u.email, u.balance, u.is_active, u.created_at, u.last_login,
               so.sportsbook_name, so.subdomain,
               COUNT(b.id) as total_bets,
               COALESCE(SUM(b.stake), 0) as total_staked,
               COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return ELSE 0 END), 0) as total_payout,
               COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake 
                               WHEN b.status = 'lost' THEN -b.stake ELSE 0 END), 0) as cumulative_profit
        FROM users u
        JOIN sportsbook_operators so ON u.sportsbook_operator_id = so.id
        LEFT JOIN bets b ON u.id = b.user_id
        GROUP BY u.id, u.username, u.email, u.balance, u.is_active, u.created_at, u.last_login, so.sportsbook_name, so.subdomain
        ORDER BY u.created_at DESC
        """
        
        users = conn.execute(users_query).fetchall()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'balance': float(user['balance']),
                'operator': user['sportsbook_name'],
                'subdomain': user['subdomain'],
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
        logger.error(f"Global users error: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@comprehensive_superadmin_bp.route('/api/superadmin/toggle-global-user', methods=['POST'])
@superadmin_required
def toggle_global_user_status():
    """Enable/disable user globally (super admin power)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        conn = get_db_connection()
        
        # Get user info
        user = conn.execute("""
            SELECT u.id, u.is_active, u.username, so.sportsbook_name
            FROM users u
            JOIN sportsbook_operators so ON u.sportsbook_operator_id = so.id
            WHERE u.id = ?
        """, (user_id,)).fetchone()
        
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
            'message': f"User {user['username']} from {user['sportsbook_name']} {'enabled' if new_status else 'disabled'} successfully",
            'new_status': new_status
        })
        
    except Exception as e:
        logger.error(f"Toggle global user error: {e}")
        return jsonify({'error': 'Failed to toggle user status'}), 500

@comprehensive_superadmin_bp.route('/api/superadmin/global-reports')
@superadmin_required
def get_global_reports():
    """Get comprehensive reports across ALL operators"""
    try:
        conn = get_db_connection()
        
        # Get comprehensive betting statistics across ALL operators
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
        """
        
        stats = conn.execute(stats_query).fetchone()
        
        # Get sport performance globally
        sport_query = """
        SELECT b.sport_name,
               COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake 
                               WHEN b.status = 'lost' THEN -b.stake ELSE 0 END), 0) as revenue
        FROM bets b
        JOIN users u ON b.user_id = u.id
        GROUP BY b.sport_name
        ORDER BY revenue DESC
        """
        
        sports = conn.execute(sport_query).fetchall()
        
        # Get top users globally
        top_users_query = """
        SELECT u.username, so.sportsbook_name, COUNT(b.id) as bet_count
        FROM users u
        JOIN sportsbook_operators so ON u.sportsbook_operator_id = so.id
        LEFT JOIN bets b ON u.id = b.user_id
        GROUP BY u.id, u.username, so.sportsbook_name
        HAVING bet_count > 0
        ORDER BY bet_count DESC
        LIMIT 10
        """
        
        top_users = conn.execute(top_users_query).fetchall()
        
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
            'top_users': [{'username': u['username'], 'operator': u['sportsbook_name'], 'bets': u['bet_count']} for u in top_users]
        })
        
    except Exception as e:
        logger.error(f"Global reports error: {e}")
        return jsonify({'error': 'Failed to get reports'}), 500

@comprehensive_superadmin_bp.route('/api/superadmin/operators')
@superadmin_required
def get_operators():
    """Get all operators for management"""
    try:
        conn = get_db_connection()
        
        operators_query = """
        SELECT so.id, so.sportsbook_name, so.subdomain, so.admin_username, so.admin_email, 
               so.is_active, so.created_at,
               COUNT(DISTINCT u.id) as total_users,
               COUNT(DISTINCT b.id) as total_bets,
               COALESCE(SUM(CASE WHEN b.status = 'won' THEN b.potential_return - b.stake 
                               WHEN b.status = 'lost' THEN -b.stake ELSE 0 END), 0) as revenue
        FROM sportsbook_operators so
        LEFT JOIN users u ON so.id = u.sportsbook_operator_id
        LEFT JOIN bets b ON u.id = b.user_id
        GROUP BY so.id, so.sportsbook_name, so.subdomain, so.admin_username, so.admin_email, so.is_active, so.created_at
        ORDER BY so.created_at DESC
        """
        
        operators = conn.execute(operators_query).fetchall()
        conn.close()
        
        operators_list = []
        for op in operators:
            operators_list.append({
                'id': op['id'],
                'sportsbook_name': op['sportsbook_name'],
                'subdomain': op['subdomain'],
                'admin_username': op['admin_username'],
                'admin_email': op['admin_email'],
                'is_active': op['is_active'],
                'created_at': op['created_at'][:10] if op['created_at'] else '',
                'total_users': op['total_users'],
                'total_bets': op['total_bets'],
                'revenue': float(op['revenue'] or 0),
                'status': 'Active' if op['is_active'] else 'Disabled'
            })
        
        return jsonify({
            'success': True,
            'operators': operators_list
        })
        
    except Exception as e:
        logger.error(f"Operators error: {e}")
        return jsonify({'error': 'Failed to get operators'}), 500

@comprehensive_superadmin_bp.route('/api/superadmin/toggle-operator', methods=['POST'])
@superadmin_required
def toggle_operator_status():
    """Enable/disable operator (super admin power)"""
    try:
        data = request.get_json()
        operator_id = data.get('operator_id')
        
        conn = get_db_connection()
        
        # Get operator info
        operator = conn.execute("""
            SELECT id, is_active, sportsbook_name FROM sportsbook_operators WHERE id = ?
        """, (operator_id,)).fetchone()
        
        if not operator:
            conn.close()
            return jsonify({'error': 'Operator not found'}), 404
        
        # Toggle operator status
        new_status = not operator['is_active']
        conn.execute("""
            UPDATE sportsbook_operators SET is_active = ? WHERE id = ?
        """, (new_status, operator_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f"Operator {operator['sportsbook_name']} {'enabled' if new_status else 'disabled'} successfully",
            'new_status': new_status
        })
        
    except Exception as e:
        logger.error(f"Toggle operator error: {e}")
        return jsonify({'error': 'Failed to toggle operator status'}), 500

@comprehensive_superadmin_bp.route('/api/superadmin/change-operator-password', methods=['POST'])
@superadmin_required
def change_operator_password():
    """Change operator admin password (super admin power)"""
    try:
        data = request.get_json()
        operator_id = data.get('operator_id')
        new_password = data.get('new_password')
        
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db_connection()
        
        # Get operator info
        operator = conn.execute("""
            SELECT id, sportsbook_name FROM sportsbook_operators WHERE id = ?
        """, (operator_id,)).fetchone()
        
        if not operator:
            conn.close()
            return jsonify({'error': 'Operator not found'}), 404
        
        # Update password
        password_hash = generate_password_hash(new_password)
        conn.execute("""
            UPDATE sportsbook_operators SET admin_password_hash = ? WHERE id = ?
        """, (password_hash, operator_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f"Password changed for {operator['sportsbook_name']} successfully"
        })
        
    except Exception as e:
        logger.error(f"Change operator password error: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

def get_comprehensive_superadmin_template():
    """Get the comprehensive super admin HTML template"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GoalServe - Super Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #f39c12 0%, #e74c3c 100%); min-height: 100vh; }
        .header { background: rgba(0,0,0,0.1); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; color: white; }
        .header h1 { font-size: 1.5rem; }
        .logout-btn { background: #c0392b; color: white; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer; }
        .container { max-width: 1600px; margin: 2rem auto; padding: 0 1rem; }
        .tabs { display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; }
        .tab { background: rgba(255,255,255,0.1); color: white; border: none; padding: 1rem 2rem; border-radius: 10px; cursor: pointer; transition: all 0.3s; }
        .tab.active { background: rgba(255,255,255,0.2); transform: translateY(-2px); }
        .tab-content { background: white; border-radius: 15px; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.1); display: none; }
        .tab-content.active { display: block; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: linear-gradient(135deg, #f39c12, #e74c3c); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem; }
        .stat-label { opacity: 0.9; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }
        .data-table th, .data-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #eee; }
        .data-table th { background: #f8f9fa; font-weight: 600; }
        .btn { padding: 0.4rem 0.8rem; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem; margin: 0 0.2rem; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-success { background: #27ae60; color: white; }
        .btn-primary { background: #3498db; color: white; }
        .btn-warning { background: #f39c12; color: white; }
        .status-active { background: #27ae60; color: white; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.8rem; }
        .status-disabled { background: #e74c3c; color: white; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.8rem; }
        .loading { text-align: center; padding: 2rem; color: #666; }
        .reports-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
        .report-card { background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #f39c12; }
        .report-title { font-weight: 600; margin-bottom: 1rem; color: #333; }
        .operator-card { background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #3498db; }
        .operator-name { font-weight: 600; color: #2c3e50; margin-bottom: 0.5rem; }
        .operator-stats { display: flex; gap: 1rem; font-size: 0.9rem; color: #666; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
        .modal-content { background: white; margin: 15% auto; padding: 2rem; width: 400px; border-radius: 10px; }
        .modal-header { font-weight: 600; margin-bottom: 1rem; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-group input { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌟 GoalServe - Super Admin Dashboard</h1>
        <div>
            <span>Global Management</span>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
    </div>

    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('global-betting-events')">📊 Global Betting Events</button>
            <button class="tab" onclick="showTab('global-user-management')">👥 Global User Management</button>
            <button class="tab" onclick="showTab('global-reports')">📈 Global Reports</button>
            <button class="tab" onclick="showTab('operator-management')">🏢 Operator Management</button>
            <button class="tab" onclick="showTab('global-report-builder')">🔧 Global Report Builder</button>
        </div>

        <!-- Global Betting Events Tab -->
        <div id="global-betting-events" class="tab-content active">
            <h2>Global Betting Events Management</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="global-total-events">-</div>
                    <div class="stat-label">Total Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="global-active-events">-</div>
                    <div class="stat-label">Active Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="global-total-liability">$0.00</div>
                    <div class="stat-label">Global Liability</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="global-total-revenue-events">$0.00</div>
                    <div class="stat-label">Global Revenue</div>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="refreshGlobalEvents()">🔄 Refresh Global Events</button>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Event ID</th>
                        <th>Sport</th>
                        <th>Event Name</th>
                        <th>Market</th>
                        <th>Operator</th>
                        <th>Total Bets</th>
                        <th>Liability</th>
                        <th>Revenue</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="global-events-table">
                    <tr><td colspan="9" class="loading">Loading global events...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Global User Management Tab -->
        <div id="global-user-management" class="tab-content">
            <h2>Global User Management</h2>
            <p style="margin-bottom: 1rem; color: #666;">Manage users across all sportsbook operators</p>
            <button class="btn btn-primary" onclick="refreshGlobalUsers()">🔄 Refresh Global Users</button>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Operator</th>
                        <th>Balance</th>
                        <th>Bets</th>
                        <th>Staked</th>
                        <th>Payout</th>
                        <th>Profit</th>
                        <th>Joined</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="global-users-table">
                    <tr><td colspan="12" class="loading">Loading global users...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Global Reports Tab -->
        <div id="global-reports" class="tab-content">
            <h2>Global Reports & Analytics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="global-total-bets-report">-</div>
                    <div class="stat-label">Global Total Bets</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="global-total-stakes-report">$0</div>
                    <div class="stat-label">Global Total Stakes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="global-total-revenue-report">$0</div>
                    <div class="stat-label">Global Total Revenue</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="global-win-rate-report">0%</div>
                    <div class="stat-label">Global Win Rate</div>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="refreshGlobalReports()">🔄 Refresh Global Reports</button>
            
            <div class="reports-grid">
                <div class="report-card">
                    <div class="report-title">📊 Global Betting Overview</div>
                    <div id="global-betting-overview">Loading...</div>
                </div>
                <div class="report-card">
                    <div class="report-title">🏆 Global Sport Performance</div>
                    <div id="global-sport-performance">Loading...</div>
                </div>
                <div class="report-card">
                    <div class="report-title">👑 Global Top Users</div>
                    <div id="global-top-users">Loading...</div>
                </div>
            </div>
        </div>

        <!-- Operator Management Tab -->
        <div id="operator-management" class="tab-content">
            <h2>🏢 Operator Management</h2>
            <p style="margin-bottom: 1rem; color: #666;">Manage all sportsbook operators</p>
            <button class="btn btn-primary" onclick="refreshOperators()">🔄 Refresh Operators</button>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Sportsbook Name</th>
                        <th>Subdomain</th>
                        <th>Admin Username</th>
                        <th>Admin Email</th>
                        <th>Users</th>
                        <th>Bets</th>
                        <th>Revenue</th>
                        <th>Created</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="operators-table">
                    <tr><td colspan="11" class="loading">Loading operators...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Global Report Builder Tab -->
        <div id="global-report-builder" class="tab-content">
            <h2>🔧 Global Report Builder</h2>
            <p>Generate comprehensive reports across all sportsbook operators</p>
            <div style="margin-top: 2rem;">
                <h3>📋 Available Global Reports</h3>
                <ul style="margin-top: 1rem; line-height: 2;">
                    <li><strong>Global Betting Summary:</strong> Betting activity across all operators</li>
                    <li><strong>Operator Performance:</strong> Revenue and performance by operator</li>
                    <li><strong>Global User Activity:</strong> User statistics across all platforms</li>
                    <li><strong>Global Financial Overview:</strong> Comprehensive financial metrics</li>
                    <li><strong>Cross-Platform Analytics:</strong> Comparative analysis between operators</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Change Password Modal -->
    <div id="passwordModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">Change Operator Password</div>
            <div class="form-group">
                <label>New Password:</label>
                <input type="password" id="newPassword" placeholder="Enter new password (min 6 characters)">
            </div>
            <div style="text-align: right;">
                <button class="btn btn-primary" onclick="saveNewPassword()">Save</button>
                <button class="btn" onclick="closePasswordModal()">Cancel</button>
            </div>
        </div>
    </div>

    <script>
        let currentOperatorId = null;
        
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load data for the tab
            if (tabName === 'global-betting-events') loadGlobalBettingEvents();
            if (tabName === 'global-user-management') loadGlobalUsers();
            if (tabName === 'global-reports') loadGlobalReports();
            if (tabName === 'operator-management') loadOperators();
        }
        
        function loadGlobalBettingEvents() {
            fetch('/api/superadmin/global-betting-events')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('global-total-events').textContent = data.total_events;
                        document.getElementById('global-active-events').textContent = data.active_events;
                        
                        const tbody = document.getElementById('global-events-table');
                        if (data.events.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #666;">No events found</td></tr>';
                        } else {
                            tbody.innerHTML = data.events.map(event => `
                                <tr>
                                    <td>${event.event_id}</td>
                                    <td>${event.sport}</td>
                                    <td>${event.event_name}</td>
                                    <td>${event.market}</td>
                                    <td><strong>${event.operator}</strong></td>
                                    <td>${event.total_bets}</td>
                                    <td>$${event.max_liability.toFixed(2)}</td>
                                    <td>$${event.max_possible_gain.toFixed(2)}</td>
                                    <td><span class="status-active">${event.status}</span></td>
                                </tr>
                            `).join('');
                        }
                    }
                })
                .catch(err => console.error('Error loading global events:', err));
        }
        
        function loadGlobalUsers() {
            fetch('/api/superadmin/global-users')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const tbody = document.getElementById('global-users-table');
                        if (data.users.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="12" style="text-align: center; color: #666;">No users found</td></tr>';
                        } else {
                            tbody.innerHTML = data.users.map(user => `
                                <tr>
                                    <td>${user.id}</td>
                                    <td>${user.username}</td>
                                    <td>${user.email}</td>
                                    <td><strong>${user.operator}</strong></td>
                                    <td>$${user.balance.toFixed(2)}</td>
                                    <td>${user.total_bets}</td>
                                    <td>$${user.total_staked.toFixed(2)}</td>
                                    <td>$${user.total_payout.toFixed(2)}</td>
                                    <td>$${user.cumulative_profit.toFixed(2)}</td>
                                    <td>${user.joined}</td>
                                    <td><span class="status-${user.is_active ? 'active' : 'disabled'}">${user.status}</span></td>
                                    <td>
                                        <button class="btn ${user.is_active ? 'btn-danger' : 'btn-success'}" 
                                                onclick="toggleGlobalUser(${user.id}, ${user.is_active})">
                                            ${user.is_active ? 'Disable' : 'Enable'}
                                        </button>
                                    </td>
                                </tr>
                            `).join('');
                        }
                    }
                })
                .catch(err => console.error('Error loading global users:', err));
        }
        
        function loadGlobalReports() {
            fetch('/api/superadmin/global-reports')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        document.getElementById('global-total-bets-report').textContent = stats.total_bets;
                        document.getElementById('global-total-stakes-report').textContent = `$${stats.total_stakes.toFixed(2)}`;
                        document.getElementById('global-total-revenue-report').textContent = `$${stats.total_revenue.toFixed(2)}`;
                        document.getElementById('global-win-rate-report').textContent = `${stats.win_rate}%`;
                        
                        // Global Betting Overview
                        document.getElementById('global-betting-overview').innerHTML = `
                            <div>Pending Bets: <strong>${stats.pending_bets}</strong></div>
                            <div>Won Bets: <strong>${stats.won_bets}</strong></div>
                            <div>Lost Bets: <strong>${stats.lost_bets}</strong></div>
                        `;
                        
                        // Global Sport Performance
                        document.getElementById('global-sport-performance').innerHTML = 
                            data.sport_performance.map(sport => 
                                `<div>${sport.sport}: <strong>$${sport.revenue.toFixed(2)}</strong></div>`
                            ).join('') || '<div>No data available</div>';
                        
                        // Global Top Users
                        document.getElementById('global-top-users').innerHTML = 
                            data.top_users.map(user => 
                                `<div>${user.username} (${user.operator}): <strong>${user.bets} bets</strong></div>`
                            ).join('') || '<div>No data available</div>';
                    }
                })
                .catch(err => console.error('Error loading global reports:', err));
        }
        
        function loadOperators() {
            fetch('/api/superadmin/operators')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const tbody = document.getElementById('operators-table');
                        if (data.operators.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: #666;">No operators found</td></tr>';
                        } else {
                            tbody.innerHTML = data.operators.map(op => `
                                <tr>
                                    <td>${op.id}</td>
                                    <td><strong>${op.sportsbook_name}</strong></td>
                                    <td>${op.subdomain}</td>
                                    <td>${op.admin_username}</td>
                                    <td>${op.admin_email}</td>
                                    <td>${op.total_users}</td>
                                    <td>${op.total_bets}</td>
                                    <td>$${op.revenue.toFixed(2)}</td>
                                    <td>${op.created_at}</td>
                                    <td><span class="status-${op.is_active ? 'active' : 'disabled'}">${op.status}</span></td>
                                    <td>
                                        <button class="btn ${op.is_active ? 'btn-danger' : 'btn-success'}" 
                                                onclick="toggleOperator(${op.id}, ${op.is_active})">
                                            ${op.is_active ? 'Disable' : 'Enable'}
                                        </button>
                                        <button class="btn btn-warning" onclick="changeOperatorPassword(${op.id})">
                                            Change Password
                                        </button>
                                    </td>
                                </tr>
                            `).join('');
                        }
                    }
                })
                .catch(err => console.error('Error loading operators:', err));
        }
        
        function toggleGlobalUser(userId, isActive) {
            fetch('/api/superadmin/toggle-global-user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    loadGlobalUsers();
                    alert(data.message);
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(err => {
                console.error('Error toggling global user:', err);
                alert('Failed to toggle user status');
            });
        }
        
        function toggleOperator(operatorId, isActive) {
            if (confirm(`Are you sure you want to ${isActive ? 'disable' : 'enable'} this operator?`)) {
                fetch('/api/superadmin/toggle-operator', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ operator_id: operatorId })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        loadOperators();
                        alert(data.message);
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(err => {
                    console.error('Error toggling operator:', err);
                    alert('Failed to toggle operator status');
                });
            }
        }
        
        function changeOperatorPassword(operatorId) {
            currentOperatorId = operatorId;
            document.getElementById('passwordModal').style.display = 'block';
            document.getElementById('newPassword').value = '';
        }
        
        function closePasswordModal() {
            document.getElementById('passwordModal').style.display = 'none';
            currentOperatorId = null;
        }
        
        function saveNewPassword() {
            const newPassword = document.getElementById('newPassword').value;
            if (!newPassword || newPassword.length < 6) {
                alert('Password must be at least 6 characters');
                return;
            }
            
            fetch('/api/superadmin/change-operator-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    operator_id: currentOperatorId,
                    new_password: newPassword
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    closePasswordModal();
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(err => {
                console.error('Error changing password:', err);
                alert('Failed to change password');
            });
        }
        
        function refreshGlobalEvents() { loadGlobalBettingEvents(); }
        function refreshGlobalUsers() { loadGlobalUsers(); }
        function refreshGlobalReports() { loadGlobalReports(); }
        function refreshOperators() { loadOperators(); }
        
        function logout() {
            if (confirm('Are you sure you want to logout?')) {
                window.location.href = '/superadmin/logout';
            }
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('passwordModal');
            if (event.target == modal) {
                closePasswordModal();
            }
        }
        
        // Load initial data
        loadGlobalBettingEvents();
    </script>
</body>
</html>
    """

