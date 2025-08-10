#!/usr/bin/env python3
"""
Interactive Database Viewer for SQLite
Browse and query database tables directly
"""

import sqlite3
import os
import sys
from datetime import datetime

class DatabaseViewer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            print("🔌 Disconnected from database")
    
    def get_tables(self):
        """Get list of all tables"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        return tables
    
    def get_table_info(self, table_name):
        """Get table structure"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return columns
    
    def get_table_data(self, table_name, limit=50, offset=0):
        """Get data from table with pagination"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
        rows = cursor.fetchall()
        return rows
    
    def get_table_count(self, table_name):
        """Get total row count for table"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        result = cursor.fetchone()
        return result['count']
    
    def execute_custom_query(self, query):
        """Execute custom SQL query"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows, None
        except Exception as e:
            return None, str(e)
    
    def display_table_structure(self, table_name):
        """Display table structure"""
        print(f"\n📋 TABLE STRUCTURE: {table_name}")
        print("=" * 60)
        columns = self.get_table_info(table_name)
        print(f"{'Column':<20} {'Type':<15} {'Not Null':<10} {'Default':<10}")
        print("-" * 60)
        for col in columns:
            not_null = "YES" if col['notnull'] else "NO"
            default = str(col['dflt_value']) if col['dflt_value'] else "NULL"
            print(f"{col['name']:<20} {col['type']:<15} {not_null:<10} {default:<10}")
    
    def display_table_data(self, table_name, limit=20):
        """Display table data"""
        print(f"\n📊 TABLE DATA: {table_name}")
        print("=" * 80)
        
        # Get table structure for headers
        columns = self.get_table_info(table_name)
        column_names = [col['name'] for col in columns]
        
        # Get data
        rows = self.get_table_data(table_name, limit)
        total_count = self.get_table_count(table_name)
        
        if not rows:
            print("No data found in table")
            return
        
        # Display headers
        header = " | ".join(f"{name:<15}" for name in column_names)
        print(header)
        print("-" * len(header))
        
        # Display rows
        for row in rows:
            row_data = []
            for col_name in column_names:
                value = row[col_name]
                if value is None:
                    value = "NULL"
                elif isinstance(value, (int, float)):
                    value = str(value)
                else:
                    value = str(value)[:15]  # Truncate long strings
                row_data.append(f"{value:<15}")
            print(" | ".join(row_data))
        
        print(f"\n📈 Showing {len(rows)} of {total_count} total rows")
    
    def interactive_menu(self):
        """Interactive menu system"""
        while True:
            print("\n" + "="*60)
            print("🗄️  DATABASE VIEWER")
            print("="*60)
            
            # Get available tables
            tables = self.get_tables()
            
            print("\n📋 Available Tables:")
            for i, table in enumerate(tables, 1):
                count = self.get_table_count(table)
                print(f"  {i}. {table} ({count} rows)")
            
            print(f"\nOptions:")
            print("  S. Show table structure")
            print("  D. Display table data")
            print("  Q. Execute custom query")
            print("  X. Exit")
            
            choice = input("\nEnter your choice: ").strip().upper()
            
            if choice == 'X':
                break
            elif choice == 'S':
                self.show_table_structure_menu(tables)
            elif choice == 'D':
                self.show_table_data_menu(tables)
            elif choice == 'Q':
                self.custom_query_menu()
            else:
                print("❌ Invalid choice. Please try again.")
    
    def show_table_structure_menu(self, tables):
        """Menu for showing table structure"""
        print("\n📋 SHOW TABLE STRUCTURE")
        print("-" * 30)
        
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        
        try:
            choice = int(input("\nSelect table number: "))
            if 1 <= choice <= len(tables):
                table_name = tables[choice - 1]
                self.display_table_structure(table_name)
            else:
                print("❌ Invalid table number")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def show_table_data_menu(self, tables):
        """Menu for showing table data"""
        print("\n📊 DISPLAY TABLE DATA")
        print("-" * 30)
        
        for i, table in enumerate(tables, 1):
            count = self.get_table_count(table)
            print(f"  {i}. {table} ({count} rows)")
        
        try:
            choice = int(input("\nSelect table number: "))
            if 1 <= choice <= len(tables):
                table_name = tables[choice - 1]
                limit = input("Enter number of rows to show (default 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                self.display_table_data(table_name, limit)
            else:
                print("❌ Invalid table number")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def custom_query_menu(self):
        """Menu for custom queries"""
        print("\n🔍 CUSTOM QUERY")
        print("-" * 20)
        print("Enter your SQL query (or 'back' to return):")
        
        while True:
            query = input("\nSQL> ").strip()
            
            if query.lower() == 'back':
                break
            
            if not query:
                continue
            
            rows, error = self.execute_custom_query(query)
            
            if error:
                print(f"❌ Error: {error}")
            else:
                if not rows:
                    print("✅ Query executed successfully. No results returned.")
                else:
                    print(f"\n📊 Results ({len(rows)} rows):")
                    print("-" * 50)
                    
                    # Display column headers
                    if rows:
                        column_names = list(rows[0].keys())
                        header = " | ".join(f"{name:<15}" for name in column_names)
                        print(header)
                        print("-" * len(header))
                        
                        # Display data
                        for row in rows:
                            row_data = []
                            for col_name in column_names:
                                value = row[col_name]
                                if value is None:
                                    value = "NULL"
                                elif isinstance(value, (int, float)):
                                    value = str(value)
                                else:
                                    value = str(value)[:15]  # Truncate long strings
                                row_data.append(f"{value:<15}")
                            print(" | ".join(row_data))

def main():
    """Main function"""
    # Database path
    db_path = os.path.join('src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("Please make sure the database file exists.")
        return
    
    print("🚀 DATABASE VIEWER")
    print("=" * 50)
    print(f"Database: {db_path}")
    
    # Create viewer and connect
    viewer = DatabaseViewer(db_path)
    if not viewer.connect():
        return
    
    try:
        # Start interactive menu
        viewer.interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        viewer.disconnect()

if __name__ == "__main__":
    main()
