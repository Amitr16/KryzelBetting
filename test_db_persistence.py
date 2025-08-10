#!/usr/bin/env python3
"""
Test script to verify database persistence
"""

import os
import sqlite3
import time

def test_database_persistence():
    """Test if database can actually store and retrieve data"""
    # Get database path from environment or use default
    database_path = os.getenv('DATABASE_PATH', 'src/database/app.db')
    
    print(f"🔍 Testing database persistence for: {database_path}")
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Environment DATABASE_PATH: {os.getenv('DATABASE_PATH', 'NOT_SET')}")
    
    # Resolve absolute path
    if not os.path.isabs(database_path):
        database_path = os.path.abspath(database_path)
    
    print(f"🔍 Absolute database path: {database_path}")
    
    try:
        # Create database and table
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_persistence (
                id INTEGER PRIMARY KEY,
                test_data TEXT,
                timestamp REAL
            )
        """)
        
        # Insert test data
        test_data = f"Test data at {time.time()}"
        cursor.execute("INSERT INTO test_persistence (test_data, timestamp) VALUES (?, ?)", 
                      (test_data, time.time()))
        
        # Commit the data
        conn.commit()
        print(f"✅ Inserted test data: {test_data}")
        
        # Verify data was stored
        cursor.execute("SELECT * FROM test_persistence ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Retrieved test data: ID={result[0]}, Data={result[1]}, Time={result[2]}")
        else:
            print(f"❌ No data retrieved!")
        
        # Close connection
        conn.close()
        
        # Wait a moment
        print("⏳ Waiting 2 seconds...")
        time.sleep(2)
        
        # Try to read the data again
        conn2 = sqlite3.connect(database_path)
        cursor2 = conn2.cursor()
        
        cursor2.execute("SELECT * FROM test_persistence ORDER BY timestamp DESC LIMIT 1")
        result2 = cursor2.fetchone()
        
        if result2:
            print(f"✅ Data still exists after reconnection: ID={result2[0]}, Data={result2[1]}, Time={result2[2]}")
        else:
            print(f"❌ Data disappeared after reconnection!")
        
        conn2.close()
        
        # Check file size
        if os.path.exists(database_path):
            file_size = os.path.getsize(database_path)
            print(f"✅ Final database file size: {file_size} bytes")
        else:
            print(f"❌ Database file no longer exists!")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_persistence()
