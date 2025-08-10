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
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Created database directory: {db_dir}")
    
    # Create database file if it doesn't exist
    if not os.path.exists(database_path):
        # Create empty database file with proper permissions
        conn = sqlite3.connect(database_path)
        conn.close()
        print(f"✅ Created database file: {database_path}")
    else:
        print(f"✅ Database file already exists: {database_path}")
    
    # Verify database file is writable
    try:
        test_conn = sqlite3.connect(database_path)
        test_conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)")
        test_conn.execute("DROP TABLE test_table")
        test_conn.close()
        print(f"✅ Database file is writable: {database_path}")
    except Exception as e:
        print(f"❌ Database file is not writable: {e}")
        raise
    
    return database_path

if __name__ == "__main__":
    init_database()
