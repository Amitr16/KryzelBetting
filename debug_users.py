#!/usr/bin/env python3
"""
Debug script to check users in database and test /api/auth/me endpoint
"""

import sqlite3
import os
import requests
import json

# Database path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')

def debug_users():
    """Debug users in database and test API"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        print("🔍 Users in database:")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Balance: {user[4]}")
        
        if not users:
            print("❌ No users found in database!")
            return
        
        # Test the /api/auth/me endpoint
        print(f"\n🔍 Testing /api/auth/me endpoint...")
        
        # First, let's try to login to get a token
        login_data = {
            'username': users[0][1],  # Use first user's username
            'password': 'password123'  # Default password
        }
        
        try:
            login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data)
            print(f"Login response status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                print(f"Login successful: {login_result}")
                
                # Get token
                token = login_result.get('token')
                if token:
                    print(f"Got token: {token[:20]}...")
                    
                    # Test /api/auth/me endpoint
                    headers = {'Authorization': f'Bearer {token}'}
                    me_response = requests.get('http://localhost:5000/api/auth/me', headers=headers)
                    print(f"/api/auth/me response status: {me_response.status_code}")
                    
                    if me_response.status_code == 200:
                        me_result = me_response.json()
                        print(f"✅ /api/auth/me response: {me_result}")
                    else:
                        print(f"❌ /api/auth/me failed: {me_response.text}")
                else:
                    print("❌ No token in login response")
            else:
                print(f"❌ Login failed: {login_response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to server. Make sure the user app is running on port 5000")
        except Exception as e:
            print(f"❌ Error testing API: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Debugging users and API...")
    debug_users()
    print("✅ Done!")
