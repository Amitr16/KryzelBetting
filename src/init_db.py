#!/usr/bin/env python3
"""
Database initialization script for Render deployment
"""

import os
import sqlite3
from pathlib import Path

def init_database():
    """Initialize database for deployment"""
    # Get database path from environment or use default
    database_path = os.getenv('DATABASE_PATH', 'src/database/app.db')
    
    # Resolve the absolute path
    if not os.path.isabs(database_path):
        # If it's a relative path, make it absolute relative to current working directory
        database_path = os.path.abspath(database_path)
    
    print(f"🔍 Database path resolved to: {database_path}")
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Environment DATABASE_PATH: {os.getenv('DATABASE_PATH', 'NOT_SET')}")
    print(f"🔍 Path exists: {os.path.exists(database_path)}")
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Created database directory: {db_dir}")
    else:
        print(f"✅ Database directory exists: {db_dir}")
    
    # Check if database file exists and its size
    if os.path.exists(database_path):
        file_size = os.path.getsize(database_path)
        print(f"✅ Database file already exists: {database_path} (size: {file_size} bytes)")
        
        # If file is very small (less than 100 bytes), it might be empty/corrupted
        if file_size < 100:
            print(f"⚠️  Database file is very small ({file_size} bytes), might be corrupted")
            # Remove and recreate
            os.remove(database_path)
            print(f"🗑️  Removed corrupted database file")
            file_exists = False
        else:
            file_exists = True
    else:
        print(f"✅ Database file does not exist, will create: {database_path}")
        file_exists = False
    
    # Create database file if it doesn't exist or was corrupted
    if not file_exists:
        # Create empty database file with proper permissions
        conn = sqlite3.connect(database_path)
        conn.close()
        print(f"✅ Created database file: {database_path}")
    else:
        print(f"✅ Using existing database file: {database_path}")
    
    # Verify database file is writable and can be opened
    try:
        test_conn = sqlite3.connect(database_path)
        test_conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)")
        test_conn.execute("DROP TABLE test_table")
        test_conn.close()
        print(f"✅ Database file is writable: {database_path}")
        
        # Check if we can actually read from the file
        if os.path.exists(database_path):
            final_size = os.path.getsize(database_path)
            print(f"✅ Final database file size: {final_size} bytes")
        else:
            print(f"❌ Database file disappeared after testing!")
            
    except Exception as e:
        print(f"❌ Database file is not writable: {e}")
        raise
    
    return database_path

if __name__ == "__main__":
    init_database()
