#!/usr/bin/env python3
"""
Simple test for /api/auth/me endpoint
"""

import requests
import json

def test_me_endpoint():
    """Test the /api/auth/me endpoint"""
    try:
        # Try to login first
        login_data = {
            'username': 'kr',
            'password': '123456'
        }
        
        print("🔍 Logging in as 'kr'...")
        login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"Login result: {login_result}")
            
            token = login_result.get('token')
            if token:
                print(f"Got token: {token[:30]}...")
                
                # Test /api/auth/me
                headers = {'Authorization': f'Bearer {token}'}
                me_response = requests.get('http://localhost:5000/api/auth/me', headers=headers)
                print(f"/api/auth/me status: {me_response.status_code}")
                print(f"/api/auth/me response: {me_response.text}")
                
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    print(f"✅ Username: {me_data.get('username')}")
                    print(f"✅ Balance: {me_data.get('balance')}")
                else:
                    print(f"❌ /api/auth/me failed")
            else:
                print("❌ No token in response")
        else:
            print(f"❌ Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Testing /api/auth/me endpoint...")
    test_me_endpoint()
    print("✅ Done!")
