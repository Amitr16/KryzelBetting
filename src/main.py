import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, redirect, session
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_session import Session
# Import database and models
from src.models.betting import db
from src.models.multitenant_models import SportsbookOperator, SuperAdmin, BetSlip, SportsbookTheme, ThemeTemplate
from src.routes.auth import auth_bp
from src.routes.json_sports import json_sports_bp
from src.routes.sports import sports_bp
from src.routes.betting import betting_bp
from src.routes.prematch_odds import prematch_odds_bp
from src.websocket_service import LiveOddsWebSocketService, init_websocket_handlers
from src.bet_settlement_service import BetSettlementService
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

# Set specific logger levels
logging.getLogger('werkzeug').setLevel(logging.INFO)
logging.getLogger('flask_socketio').setLevel(logging.INFO)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Enable CORS for all routes
CORS(app, origins="*")

# Ensure proper encoding handling
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'goalserve-sportsbook-secret-key-change-in-production')

# Database configuration - use environment variable or default to local path
database_path = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'database', 'app.db'))

# Resolve absolute path for consistency
if not os.path.isabs(database_path):
    database_path = os.path.abspath(database_path)

print(f"🔍 Main app database path: {database_path}")
print(f"🔍 Main app working directory: {os.getcwd()}")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Initialize Flask-Session
Session(app)

# Ensure proper UTF-8 handling
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Import sportsbook registration routes
from src.routes.sportsbook_registration import sportsbook_bp
from src.routes.multitenant_routing import multitenant_bp
from src.routes.clean_multitenant_routing import clean_multitenant_bp
from src.routes.superadmin import superadmin_bp
from src.routes.tenant_admin import tenant_admin_bp
from src.routes.branding import branding_bp
from src.routes.tenant_auth import tenant_auth_bp

# Import comprehensive admin blueprints
from src.routes.comprehensive_admin import comprehensive_admin_bp
from src.routes.comprehensive_superadmin import comprehensive_superadmin_bp
from src.routes.rich_admin_interface import rich_admin_bp
from src.routes.rich_superadmin_interface1 import rich_superadmin_bp

# Import theme customization blueprint
from src.routes.theme_customization import theme_bp

# Add debug logging for blueprint registration
print("🔍 Registering blueprints...")
app.register_blueprint(rich_admin_bp)  # Rich admin interface first
print("✅ Registered rich_admin_bp")
app.register_blueprint(rich_superadmin_bp)
print("✅ Registered rich_superadmin_bp")
app.register_blueprint(theme_bp)  # Theme customization routes
print("✅ Registered theme_bp")
app.register_blueprint(auth_bp, url_prefix='/api/auth')
print("✅ Registered auth_bp")
app.register_blueprint(json_sports_bp, url_prefix='/api/sports')
print("✅ Registered json_sports_bp")
app.register_blueprint(sports_bp, url_prefix='/api')
print("✅ Registered sports_bp")
app.register_blueprint(betting_bp, url_prefix='/api/betting')
print("✅ Registered betting_bp")
app.register_blueprint(prematch_odds_bp, url_prefix='/api/prematch-odds')
print("✅ Registered prematch_odds_bp")
# app.register_blueprint(multitenant_bp)  # Disable old multitenant routing - REMOVED
app.register_blueprint(clean_multitenant_bp)  # New clean URL routing - REGISTER BEFORE sportsbook_bp - FIXES ADMIN 404
print("✅ Registered clean_multitenant_bp")
app.register_blueprint(sportsbook_bp, url_prefix='/api')  # Move this AFTER clean_multitenant_bp
print("✅ Registered sportsbook_bp")
app.register_blueprint(superadmin_bp)
print("✅ Registered superadmin_bp")
app.register_blueprint(tenant_admin_bp)
print("✅ Registered tenant_admin_bp")
app.register_blueprint(branding_bp)
print("✅ Registered branding_bp")
app.register_blueprint(tenant_auth_bp)
print("✅ Registered tenant_auth_bp")
app.register_blueprint(comprehensive_admin_bp)
print("✅ Registered comprehensive_admin_bp")
app.register_blueprint(comprehensive_superadmin_bp)
print("✅ Registered comprehensive_superadmin_bp")
print("🔍 All blueprints registered successfully!")

# Initialize database
db.init_app(app)

# Initialize database for deployment (only once)
_database_initialized = False

def initialize_database_once():
    global _database_initialized
    if _database_initialized:
        print("✅ Database already initialized, skipping...")
        return
    
    try:
        from src.init_db import init_database
        database_path = init_database()
        print(f"✅ Database initialized at: {database_path}")
        
        # Ensure database is ready before creating tables
        with app.app_context():
            # Force database connection to ensure file exists
            db.engine.connect()
            print("✅ Database connection established")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create default superadmin user
            try:
                from src.models.multitenant_models import SuperAdmin
                from werkzeug.security import generate_password_hash
                
                # Check if superadmin already exists
                existing_superadmin = SuperAdmin.query.filter_by(username='superadmin').first()
                if not existing_superadmin:
                    superadmin = SuperAdmin(
                        username='superadmin',
                        password_hash=generate_password_hash('KryzelAdmin!@#123'),
                        email='superadmin@goalserve.com',
                        is_active=True,
                        permissions='{"all": true}'
                    )
                    db.session.add(superadmin)
                    db.session.commit()
                    print("✅ Default superadmin created (username: superadmin, password: KryzelAdmin!@#123)")
                else:
                    print("ℹ️  Superadmin already exists")
            except Exception as e:
                print(f"⚠️  Could not create superadmin: {e}")
            
        _database_initialized = True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Try to create tables anyway
        with app.app_context():
            try:
                db.create_all()
                print("✅ Database tables created (fallback)")
                
                # Try to create superadmin in fallback mode too
                try:
                    from src.models.multitenant_models import SuperAdmin
                    from werkzeug.security import generate_password_hash
                    
                    existing_superadmin = SuperAdmin.query.filter_by(username='superadmin').first()
                    if not existing_superadmin:
                        superadmin = SuperAdmin(
                            username='superadmin',
                            password_hash=generate_password_hash('KryzelAdmin!@#123'),
                            email='superadmin@goalserve.com',
                            is_active=True,
                            permissions='{"all": true}'
                        )
                        db.session.add(superadmin)
                        db.session.commit()
                        print("✅ Default superadmin created in fallback mode")
                except Exception as e3:
                    print(f"⚠️  Could not create superadmin in fallback mode: {e3}")
                
                _database_initialized = True
            except Exception as e2:
                print(f"❌ Fallback table creation also failed: {e2}")

# Initialize database
initialize_database_once()

# Initialize WebSocket service
live_odds_service = LiveOddsWebSocketService(socketio)
init_websocket_handlers(socketio, live_odds_service)

# Initialize bet settlement service
bet_settlement_service = BetSettlementService(app)

# Start the bet settlement service automatically when the module is imported
# Temporarily disabled to prevent database locking issues
try:
    # bet_settlement_service.start()  # Temporarily disabled
    logging.info("✅ Bet settlement service created but not started (disabled to prevent DB locks)")
except Exception as e:
    logging.error(f"❌ Failed to create bet settlement service: {e}")

def ensure_settlement_service_running():
    """Ensure the settlement service is running, restart if needed"""
    if not bet_settlement_service.running:
        logging.warning("🔄 Settlement service not running, attempting restart...")
        try:
            success = bet_settlement_service.start()
            if success:
                logging.info("✅ Settlement service restarted successfully")
            else:
                logging.error("❌ Failed to restart settlement service")
        except Exception as e:
            logging.error(f"❌ Error restarting settlement service: {e}")

# Schedule periodic health checks for settlement service
import atexit
import signal

def cleanup_services():
    """Cleanup services on shutdown"""
    logging.info("🛑 Shutting down services...")
    bet_settlement_service.stop()
    live_odds_service.stop()

atexit.register(cleanup_services)

# Handle graceful shutdown
def signal_handler(signum, frame):
    logging.info(f"🛑 Received signal {signum}, shutting down gracefully...")
    cleanup_services()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'GoalServe Sports Betting Platform',
        'version': '1.0.0',
        'websocket_clients': live_odds_service.get_connected_clients_count()
    }

@app.route('/api/websocket/status', methods=['GET'])
def websocket_status():
    """WebSocket service status endpoint"""
    return {
        'service_running': live_odds_service.running,
        'connected_clients': live_odds_service.get_connected_clients_count(),
        'update_interval': live_odds_service.update_interval,
        'critical_matches': live_odds_service.get_critical_matches(),
        'current_update_frequency': '1 second' if live_odds_service.critical_matches else f'{live_odds_service.update_interval} seconds'
    }

@app.route('/api/websocket/start', methods=['POST'])
def start_websocket_service():
    """Start the WebSocket live odds service"""
    try:
        live_odds_service.start()
        return {'status': 'started', 'message': 'Live odds WebSocket service started'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/websocket/stop', methods=['POST'])
def stop_websocket_service():
    """Stop the WebSocket live odds service"""
    try:
        live_odds_service.stop()
        return {'status': 'stopped', 'message': 'Live odds WebSocket service stopped'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/settlement/status', methods=['GET'])
def settlement_status():
    """Get bet settlement service status"""
    return {
        'service_running': bet_settlement_service.running,
        'check_interval': bet_settlement_service.check_interval,
        'stats': bet_settlement_service.get_settlement_stats()
    }

@app.route('/api/settlement/start', methods=['POST'])
def start_settlement_service():
    """Start the automatic bet settlement service"""
    try:
        bet_settlement_service.start()
        return {'status': 'started', 'message': 'Automatic bet settlement service started'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/settlement/stop', methods=['POST'])
def stop_settlement_service():
    """Stop the automatic bet settlement service"""
    try:
        bet_settlement_service.stop()
        return {'status': 'stopped', 'message': 'Automatic bet settlement service stopped'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/settlement/force/<match_name>', methods=['POST'])
def force_settle_match(match_name):
    """Force settlement for a specific match"""
    try:
        bet_settlement_service.force_settle_match(match_name)
        return {'status': 'success', 'message': f'Force settlement triggered for {match_name}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/monitoring/dashboard', methods=['GET'])
def monitoring_dashboard():
    """Comprehensive monitoring dashboard"""
    try:
        # Get settlement service stats
        settlement_stats = bet_settlement_service.get_settlement_stats()
        
        # Get WebSocket service stats
        websocket_stats = {
            'service_running': live_odds_service.running,
            'connected_clients': live_odds_service.get_connected_clients_count(),
            'update_interval': live_odds_service.update_interval,
            'critical_matches': live_odds_service.get_critical_matches()
        }
        
        # Get database stats
        from src.models.betting import Bet, User, Transaction
        with app.app_context():
            db_stats = {
                'total_users': User.query.count(),
                'total_bets': Bet.query.count(),
                'pending_bets': Bet.query.filter_by(status='pending').count(),
                'won_bets': Bet.query.filter_by(status='won').count(),
                'lost_bets': Bet.query.filter_by(status='lost').count(),
                'void_bets': Bet.query.filter_by(status='void').count(),
                'total_transactions': Transaction.query.count()
            }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'settlement_service': settlement_stats,
                'websocket_service': websocket_stats
            },
            'database': db_stats,
            'system': {
                'python_version': sys.version,
                'platform': sys.platform
            }
        }
        
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/debug/sportsbooks', methods=['GET'])
def debug_sportsbooks():
    """Debug endpoint to check what sportsbooks exist in the database"""
    try:
        from src.models.multitenant_models import SportsbookOperator
        with app.app_context():
            sportsbooks = SportsbookOperator.query.all()
            sportsbook_list = []
            for sb in sportsbooks:
                sportsbook_list.append({
                    'id': sb.id,
                    'subdomain': sb.subdomain,
                    'sportsbook_name': sb.sportsbook_name,
                    'is_active': sb.is_active,
                    'created_at': sb.created_at.isoformat() if sb.created_at else None
                })
            
            return {
                'status': 'success',
                'count': len(sportsbook_list),
                'sportsbooks': sportsbook_list
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }, 500

@app.route('/api/debug/superadmin', methods=['GET'])
def debug_superadmin():
    """Debug endpoint to check superadmin in database"""
    try:
        from src.models.multitenant_models import SuperAdmin
        with app.app_context():
            superadmins = SuperAdmin.query.all()
            superadmin_list = []
            for sa in superadmins:
                superadmin_list.append({
                    'id': sa.id,
                    'username': sa.username,
                    'email': sa.email,
                    'is_active': sa.is_active,
                    'created_at': sa.created_at.isoformat() if sa.created_at else None
                })
            
            return {
                'status': 'success',
                'count': len(superadmin_list),
                'superadmins': superadmin_list
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }, 500

@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Internal server error'}, 500

@app.errorhandler(UnicodeDecodeError)
def unicode_decode_error(error):
    return {'error': f'Unicode decoding error: {str(error)}'}, 500

# Proxy route for Google OAuth callback to match Google console redirect URI
@app.route('/auth/google/callback', methods=['GET'])
def google_oauth_callback_proxy():
    # Forward all query params to the actual API callback under the blueprint
    query_string = request.query_string.decode() if request.query_string else ''
    target = '/api/auth/google/callback'
    if query_string:
        target = f"{target}?{query_string}"
    return redirect(target, code=302)

# Explicit route for the standalone login page to avoid redirect loops
@app.route('/login')
def serve_login():
    static_folder_path = app.static_folder
    if static_folder_path is None:
        logging.error("Static folder not configured")
        return "Static folder not configured", 404
    
    if not os.path.exists(static_folder_path):
        logging.error(f"Static folder does not exist: {static_folder_path}")
        return "Static folder not found", 404
    
    try:
        return send_from_directory(static_folder_path, 'login.html')
    except Exception as e:
        logging.error(f"Error serving login.html: {e}")
        return f"Error serving login page: {str(e)}", 500

# Catch-all route for static files - must be after all API routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Debug logging to trace route interception
    print(f"🔍 Catch-all route intercepted: '{path}'")
    
    # Don't serve static files for API routes
    if path.startswith('api/'):
        print(f"❌ API route intercepted: {path}")
        return "API endpoint not found", 404
    
    # Don't intercept any admin routes - let blueprints handle them completely
    # Check for both /admin/ and /<subdomain>/admin/ patterns
    if path.startswith('admin/') or '/admin/' in path:
        print(f"❌ Admin route intercepted by catch-all: {path}")
        return "Admin route should be handled by blueprint", 404
    
        # Handle sportsbook routes - these are handled by the multitenant blueprint
    if path.startswith('sportsbook/'):
        # These routes are handled by the multitenant blueprint
        # This should not be reached, but just in case
        return "Sportsbook route should be handled by blueprint", 404
        
    static_folder_path = app.static_folder
    if static_folder_path is None:
        logging.error("Static folder not configured")
        return "Static folder not configured", 404
    
    if not os.path.exists(static_folder_path):
        logging.error(f"Static folder does not exist: {static_folder_path}")
        return "Static folder not found", 404

    # Special-case for login without extension
    if path == 'login' or path == 'login.html':
        try:
            return send_from_directory(static_folder_path, 'login.html')
        except Exception as e:
            logging.error(f"Error serving login.html: {e}")
            return f"Error serving login page: {str(e)}", 500
    
    # Special case for sportsbook registration
    if path == 'register-sportsbook' or path == 'register-sportsbook.html':
        try:
            return send_from_directory(static_folder_path, 'register-sportsbook.html')
        except Exception as e:
            logging.error(f"Error serving register-sportsbook.html: {e}")
            return f"Error serving registration page: {str(e)}", 500

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        try:
            return send_from_directory(static_folder_path, path)
        except Exception as e:
            logging.error(f"Error serving static file {path}: {e}")
            return f"Error serving file: {str(e)}", 500
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            try:
                return send_from_directory(static_folder_path, 'index.html')
            except Exception as e:
                logging.error(f"Error serving index.html: {e}")
                return f"Error serving index.html: {str(e)}", 500
        else:
            logging.error(f"index.html not found at {index_path}")
            return "index.html not found", 404

@app.route('/api/fix/krz-sportsbook', methods=['POST'])
def fix_krz_sportsbook():
    """Temporary endpoint to fix the krz sportsbook is_active field"""
    try:
        from src.models.multitenant_models import SportsbookOperator
        with app.app_context():
            # Find the krz sportsbook
            sportsbook = SportsbookOperator.query.filter_by(subdomain='krz').first()
            if sportsbook:
                sportsbook.is_active = True
                db.session.commit()
                return {
                    'status': 'success',
                    'message': 'krz sportsbook is now active',
                    'sportsbook': {
                        'id': sportsbook.id,
                        'subdomain': sportsbook.subdomain,
                        'sportsbook_name': sportsbook.sportsbook_name,
                        'is_active': sportsbook.is_active
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': 'krz sportsbook not found'
                }, 404
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }, 500

if __name__ == '__main__':
    print("🚀 Starting GoalServe Sports Betting Platform...")
    print("🔧 Environment: Python", sys.version)
    try:
        print("🔧 Flask version:", Flask.__version__)
    except AttributeError:
        print("🔧 Flask version: Unknown (__version__ attribute not available)")
    print("🔧 Working directory:", os.getcwd())
    print("🔧 Static folder:", app.static_folder)
    
    # Start the WebSocket service
    try:
        live_odds_service.start()
        print("✅ WebSocket service started successfully")
    except Exception as e:
        print(f"❌ Failed to start WebSocket service: {e}")
        logging.error(f"Failed to start WebSocket service: {e}")
    
    # Start the automatic bet settlement service
    try:
        bet_settlement_service.start()
        print("✅ Bet settlement service started successfully")
        
        # Verify the service is running
        if bet_settlement_service.running:
            print(f"✅ Settlement service is running (check interval: {bet_settlement_service.check_interval}s)")
        else:
            print("❌ Settlement service failed to start")
            
    except Exception as e:
        print(f"❌ Failed to start bet settlement service: {e}")
        logging.error(f"Failed to start bet settlement service: {e}")
    
    print("🌐 Starting Flask application...")
    print("🔧 Debug mode: True")
    print("🔧 Host: 0.0.0.0")
    print("🔧 Port: 5000")
    
    # Run the application with SocketIO
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"❌ Failed to start Flask application: {e}")
        logging.error(f"Failed to start Flask application: {e}")
        sys.exit(1)

