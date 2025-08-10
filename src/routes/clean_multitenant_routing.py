"""
Clean multi-tenant routing system with improved URL structure
/<subdomain> - customer betting interface
/<subdomain>/login - customer login/register
/<subdomain>/admin - admin interface
"""

from flask import Blueprint, request, redirect, render_template_string
import sqlite3
import os

clean_multitenant_bp = Blueprint('clean_multitenant', __name__)

# Database configuration - use environment variable or default to local path
DATABASE_PATH = os.getenv('DATABASE_PATH', 'src/database/app.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def validate_subdomain(subdomain):
    """Validate subdomain and return operator info"""
    conn = get_db_connection()
    
    operator = conn.execute("""
        SELECT id, sportsbook_name, login, subdomain, is_active, email
        FROM sportsbook_operators 
        WHERE subdomain = ?
    """, (subdomain,)).fetchone()
    
    conn.close()
    
    if not operator:
        return None, "Sportsbook not found"
    
    if not operator['is_active']:
        return None, "This sportsbook is currently disabled"
    
    return dict(operator), None

# Customer betting interface - clean URL
@clean_multitenant_bp.route('/<subdomain>')
@clean_multitenant_bp.route('/<subdomain>/')
def sportsbook_home(subdomain):
    """Serve the customer betting interface for a specific sportsbook"""
    from src.routes.branding import get_operator_branding, generate_custom_css, generate_custom_js
    
    # Get operator branding
    branding = get_operator_branding(subdomain)
    if not branding:
        return "Sportsbook not found or inactive", 404
    
    # Serve the main betting interface with operator branding
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    
    try:
        html_path = os.path.join(static_folder, 'index.html')
        print(f"📁 Reading HTML file: {html_path}")
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Successfully read HTML file, content length: {len(content)} characters")
        
        operator = branding['operator']
        
        # Replace basic branding
        content = content.replace('GoalServe Sports Betting Platform', f"{operator['name']} - Sports Betting")
        content = content.replace('GoalServe', operator['name'])
        
        # Inject custom CSS
        custom_css = generate_custom_css(branding)
        content = content.replace('</head>', f'{custom_css}</head>')
        
        # Fix authentication redirects to maintain operator context
        auth_fix_js = f"""
        <script>
        // Override authentication redirects to maintain operator context
        window.OPERATOR_SUBDOMAIN = '{subdomain}';
        
        // Override the original auth functions
        window.showLogin = function() {{ window.location.href = '/{subdomain}/login'; }};
        window.showRegister = function() {{ window.location.href = '/{subdomain}/login'; }};
        
        // Fix the DOMContentLoaded authentication check
        document.addEventListener('DOMContentLoaded', function() {{
            const originalHandler = arguments.callee;
            const token = localStorage.getItem('token');
            if (!token) {{ 
                window.location.href = '/{subdomain}/login'; 
                return; 
            }}
            // Continue with normal authentication but with operator context
            fetch(`/api/auth/${{'{subdomain}'}}/profile`, {{ 
                headers: {{ 'Authorization': `Bearer ${{token}}` }} 
            }})
            .then(r => {{ 
                if (!r.ok) throw new Error('Invalid token'); 
                return r.json(); 
            }})
            .then(data => {{
                currentUser = data.user;
                document.getElementById('mainApp').style.display = 'block';
                if (typeof initWebSocket === 'function') initWebSocket();
                loadSports();
                // Don't start auto-refresh for admin pages - it causes constant reloading
                // if (typeof startOddsAutoRefresh === 'function') startOddsAutoRefresh();
                updateBettingMarkets();
                updateBetModeDisplay();
            }})
            .catch(() => {{ 
                localStorage.removeItem('token'); 
                window.location.href = '/{subdomain}/login'; 
            }});
        }}, true);
        </script>
        """
        
        # Inject custom JavaScript
        custom_js = generate_custom_js(branding)
        content = content.replace('</body>', f'{auth_fix_js}{custom_js}</body>')
        
        return content
        
    except FileNotFoundError:
        print(f"❌ HTML file not found: {html_path}")
        return "Betting interface not found", 500
    except UnicodeDecodeError as e:
        print(f"❌ Unicode decoding error: {e}")
        print(f"❌ File path: {html_path}")
        return f"Error reading betting interface: {str(e)}", 500
    except Exception as e:
        print(f"❌ Unexpected error reading HTML file: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return f"Error reading betting interface: {str(e)}", 500

# Customer login/register page
@clean_multitenant_bp.route('/<subdomain>/login')
def sportsbook_login(subdomain):
    """Serve operator-specific login/register page"""
    operator, error = validate_subdomain(subdomain)
    if not operator:
        return f"Error: {error}", 404
    
    # Create a branded login/register page
    login_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{operator['sportsbook_name']} - Login</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: #ffffff;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }}
            .login-container {{
                background: rgba(26, 26, 46, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 2rem;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            }}
            .logo {{
                text-align: center;
                margin-bottom: 2rem;
            }}
            .logo h1 {{
                color: #4ade80;
                font-size: 1.5rem;
                margin: 0;
            }}
            .form-group {{
                margin-bottom: 1rem;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 0.5rem;
                color: #e5e7eb;
            }}
            .form-group input {{
                width: 100%;
                padding: 0.75rem;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-size: 1rem;
                box-sizing: border-box;
            }}
            .form-group input:focus {{
                outline: none;
                border-color: #4ade80;
            }}
            .btn {{
                width: 100%;
                padding: 0.75rem;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            .btn-primary {{
                background: #4ade80;
                color: #000;
            }}
            .btn-primary:hover {{
                background: #22c55e;
            }}
            .toggle-form {{
                text-align: center;
                margin-top: 1rem;
            }}
            .toggle-form a {{
                color: #4ade80;
                text-decoration: none;
            }}
            .toggle-form a:hover {{
                text-decoration: underline;
            }}
            .hidden {{
                display: none;
            }}
            .message {{
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                text-align: center;
            }}
            .message.success {{
                background: rgba(34, 197, 94, 0.2);
                border: 1px solid #22c55e;
                color: #22c55e;
            }}
            .message.error {{
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid #ef4444;
                color: #ef4444;
            }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">
                <h1>{operator['sportsbook_name']}</h1>
                <p>Sports Betting Platform</p>
            </div>
            
            <div id="message" class="message hidden"></div>
            
            <!-- Login Form -->
            <div id="loginForm">
                <h2>Login</h2>
                <form onsubmit="handleLogin(event)">
                    <div class="form-group">
                        <label>Username or Email</label>
                        <input type="text" id="loginUsername" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="loginPassword" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                </form>
                <div class="toggle-form">
                    <p>Don't have an account? <a href="#" onclick="showRegisterForm()">Register here</a></p>
                </div>
            </div>
            
            <!-- Register Form -->
            <div id="registerForm" class="hidden">
                <h2>Register</h2>
                <form onsubmit="handleRegister(event)">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="registerUsername" required>
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="registerEmail" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="registerPassword" required minlength="6">
                    </div>
                    <button type="submit" class="btn btn-primary">Create Account</button>
                </form>
                <div class="toggle-form">
                    <p>Already have an account? <a href="#" onclick="showLoginForm()">Login here</a></p>
                </div>
            </div>
        </div>
        
        <script>
            const SUBDOMAIN = '{subdomain}';
            const OPERATOR_ID = {operator['id']};
            
            function showMessage(text, type) {{
                const messageEl = document.getElementById('message');
                messageEl.textContent = text;
                messageEl.className = `message ${{type}}`;
                messageEl.classList.remove('hidden');
                
                setTimeout(() => {{
                    messageEl.classList.add('hidden');
                }}, 5000);
            }}
            
            function showLoginForm() {{
                document.getElementById('loginForm').classList.remove('hidden');
                document.getElementById('registerForm').classList.add('hidden');
            }}
            
            function showRegisterForm() {{
                document.getElementById('loginForm').classList.add('hidden');
                document.getElementById('registerForm').classList.remove('hidden');
            }}
            
            async function handleLogin(event) {{
                event.preventDefault();
                
                const username = document.getElementById('loginUsername').value;
                const password = document.getElementById('loginPassword').value;
                
                try {{
                    const response = await fetch(`/api/auth/${{SUBDOMAIN}}/login`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ username, password }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        localStorage.setItem('token', data.token);
                        showMessage(data.message, 'success');
                        setTimeout(() => {{
                            window.location.href = `/${{SUBDOMAIN}}`;
                        }}, 1000);
                    }} else {{
                        showMessage(data.error || 'Login failed', 'error');
                    }}
                }} catch (error) {{
                    showMessage('Login failed: ' + error.message, 'error');
                }}
            }}
            
            async function handleRegister(event) {{
                event.preventDefault();
                
                const username = document.getElementById('registerUsername').value;
                const email = document.getElementById('registerEmail').value;
                const password = document.getElementById('registerPassword').value;
                
                try {{
                    const response = await fetch(`/api/auth/${{SUBDOMAIN}}/register`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ username, email, password }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        showMessage(data.message, 'success');
                        setTimeout(() => {{
                            showLoginForm();
                        }}, 2000);
                    }} else {{
                        showMessage(data.error || 'Registration failed', 'error');
                    }}
                }} catch (error) {{
                    showMessage('Registration failed: ' + error.message, 'error');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return login_html

# Admin interface - serve directly at /<subdomain>/admin
@clean_multitenant_bp.route('/<subdomain>/admin')
@clean_multitenant_bp.route('/<subdomain>/admin/')
def sportsbook_admin(subdomain):
    """Serve rich admin interface directly at /<subdomain>/admin"""
    # Check if admin is authenticated using the correct session keys
    from flask import session
    if not (session.get('operator_id') and session.get('operator_subdomain') == subdomain):
        return redirect(f'/{subdomain}/admin/login')
    
    # Serve the rich admin interface directly
    from src.routes.rich_admin_interface import serve_rich_admin_template
    return serve_rich_admin_template(subdomain)

# Admin login page
@clean_multitenant_bp.route('/<subdomain>/admin/login')
def sportsbook_admin_login(subdomain):
    """Serve admin login page"""
    operator, error = validate_subdomain(subdomain)
    if not operator:
        return f"Error: {error}", 404
    
    # Create branded admin login page
    admin_login_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{operator['sportsbook_name']} - Admin Login</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: #ffffff;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }}
            .login-container {{
                background: rgba(26, 26, 46, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 2rem;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            }}
            .logo {{
                text-align: center;
                margin-bottom: 2rem;
            }}
            .logo h1 {{
                color: #f39c12;
                font-size: 1.5rem;
                margin: 0;
            }}
            .form-group {{
                margin-bottom: 1rem;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 0.5rem;
                color: #e5e7eb;
            }}
            .form-group input {{
                width: 100%;
                padding: 0.75rem;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-size: 1rem;
                box-sizing: border-box;
            }}
            .form-group input:focus {{
                outline: none;
                border-color: #f39c12;
            }}
            .btn {{
                width: 100%;
                padding: 0.75rem;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s ease;
                background: #f39c12;
                color: #000;
            }}
            .btn:hover {{
                background: #e67e22;
            }}
            .message {{
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                text-align: center;
            }}
            .message.error {{
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid #ef4444;
                color: #ef4444;
            }}
            .hidden {{
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">
                <h1>{operator['sportsbook_name']}</h1>
                <p>Admin Panel</p>
            </div>
            
            <div id="message" class="message hidden"></div>
            
            <form onsubmit="handleAdminLogin(event)">
                <div class="form-group">
                    <label>Admin Username</label>
                    <input type="text" id="adminUsername" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="adminPassword" required>
                </div>
                <button type="submit" class="btn">Sign In</button>
            </form>
        </div>
        
        <script>
            const SUBDOMAIN = '{subdomain}';
            
            function showMessage(text, type) {{
                const messageEl = document.getElementById('message');
                messageEl.textContent = text;
                messageEl.className = `message ${{type}}`;
                messageEl.classList.remove('hidden');
                
                setTimeout(() => {{
                    messageEl.classList.add('hidden');
                }}, 5000);
            }}
            
            async function handleAdminLogin(event) {{
                event.preventDefault();
                
                const username = document.getElementById('adminUsername').value;
                const password = document.getElementById('adminPassword').value;
                
                try {{
                    const response = await fetch(`/${{SUBDOMAIN}}/admin/api/login`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ username, password }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        window.location.href = `/${{SUBDOMAIN}}/admin`;
                    }} else {{
                        showMessage(data.error || 'Login failed', 'error');
                    }}
                }} catch (error) {{
                    showMessage('Login failed: ' + error.message, 'error');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return admin_login_html

# Admin login API
@clean_multitenant_bp.route('/<subdomain>/admin/api/login', methods=['POST'])
def admin_login_api(subdomain):
    """Handle admin login"""
    from flask import request, session, jsonify
    
    operator, error = validate_subdomain(subdomain)
    if not operator:
        return jsonify({'success': False, 'error': error}), 404
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Verify admin credentials
    if username == operator['login'] and password:  # Need to add password verification
        # Use consistent session keys that match the rest of the application
        session['operator_id'] = operator['id']
        session['operator_subdomain'] = subdomain
        session['admin_username'] = username
        session['admin_id'] = operator['id']  # Keep for backward compatibility
        session['admin_subdomain'] = subdomain  # Keep for backward compatibility
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

# Admin logout route
@clean_multitenant_bp.route('/<subdomain>/admin/logout')
def admin_logout(subdomain):
    """Handle admin logout and redirect to admin login"""
    from flask import session, redirect
    
    # Clear the session
    session.clear()
    
    # Redirect to admin login page for this subdomain
    return redirect(f'/{subdomain}/admin/login')

# Theme customizer for specific operator
@clean_multitenant_bp.route('/<subdomain>/admin/theme-customizer')
def sportsbook_theme_customizer(subdomain):
    """Serve theme customizer for specific operator"""
    from flask import session
    
    # Check if admin is authenticated for this subdomain
    if not (session.get('operator_id') and session.get('operator_subdomain') == subdomain):
        return redirect(f'/{subdomain}/admin/login')
    
    operator, error = validate_subdomain(subdomain)
    if not operator:
        return f"Error: {error}", 404
    
    # Read the theme customizer HTML file and customize it for this operator
    import os
    html_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'theme-customizer.html')
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Customize the theme customizer for this specific operator
        html_content = html_content.replace('GoalServe Platform', f"{operator['sportsbook_name']} Platform")
        html_content = html_content.replace('Your Sportsbook', operator['sportsbook_name'])
        
        # Update API endpoints to be subdomain-specific
        html_content = html_content.replace('/api/load-theme/', f'/api/load-theme/{subdomain}')
        html_content = html_content.replace('/api/save-theme/', f'/api/save-theme/{subdomain}')
        html_content = html_content.replace('/api/theme-css/', f'/api/theme-css/{subdomain}')
        
        # Add subdomain context to JavaScript
        subdomain_js = f"""
        <script>
        // Set subdomain context for theme customizer
        window.OPERATOR_SUBDOMAIN = '{subdomain}';
        window.OPERATOR_NAME = '{operator['sportsbook_name']}';
        
        // Override API calls to use subdomain-specific endpoints
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {{
            if (url.startsWith('/api/save-theme/') && !url.includes('{subdomain}')) {{
                url = `/api/save-theme/{subdomain}`;
            }}
            if (url.startsWith('/api/load-theme/') && !url.includes('{subdomain}')) {{
                url = `/api/load-theme/{subdomain}`;
            }}
            return originalFetch(url, options);
        }};
        </script>
        """
        
        html_content = html_content.replace('</head>', f'{subdomain_js}</head>')
        
        return html_content, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        print(f"Error serving theme customizer: {e}")
        return "Theme customizer not available", 500

