#!/usr/bin/env python3
"""
Script to create a super admin account
"""

import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime
import sys

DATABASE_PATH = 'src/database/app.db'

def create_superadmin(username, password, email=None):
    """Create a super admin account"""
    
    if len(password) < 8:
        print("Error: Password must be at least 8 characters long")
        return False
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Check if super admin already exists
        existing = conn.execute(
            "SELECT id FROM super_admins WHERE username = ?", 
            (username,)
        ).fetchone()
        
        if existing:
            print(f"Error: Super admin with username '{username}' already exists")
            conn.close()
            return False
        
        # Create super admin
        password_hash = generate_password_hash(password)
        
        conn.execute("""
            INSERT INTO super_admins (username, password_hash, email, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, email, True, datetime.utcnow()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Super admin '{username}' created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email or 'Not provided'}")
        print(f"   Login URL: http://localhost:5000/superadmin")
        
        return True
        
    except Exception as e:
        print(f"Error creating super admin: {str(e)}")
        return False

def main():
    """Main function"""
    print("🔧 GoalServe Super Admin Account Creator")
    print("=" * 50)
    
    # Get input from user
    username = input("Enter super admin username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return
    
    password = input("Enter super admin password (min 8 chars): ").strip()
    if not password:
        print("Error: Password cannot be empty")
        return
    
    email = input("Enter email (optional): ").strip()
    if not email:
        email = None
    
    print("\nCreating super admin account...")
    success = create_superadmin(username, password, email)
    
    if success:
        print("\n🎉 Super admin account created successfully!")
        print("\nYou can now login at: http://localhost:5000/superadmin")
    else:
        print("\n❌ Failed to create super admin account")

if __name__ == "__main__":
    main()

