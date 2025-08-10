#!/usr/bin/env python3
"""
Query the bets table to see current sport_name values
"""

import sqlite3
import os

def query_bets_table():
    """Query and display all bets with their sport names"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"🔍 Querying bets table from: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        print("\n📋 TABLE STRUCTURE:")
        print("=" * 50)
        cursor.execute("PRAGMA table_info(bets)")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
        
        # Show all bets with sport names and markets
        print("\n🎯 ALL BETS WITH SPORT NAMES AND MARKETS:")
        print("=" * 140)
        print(f"{'ID':<4} {'Match ID':<8} {'Match Name':<30} {'Sport':<10} {'Market':<15} {'Status':<10} {'Type':<8} {'Timing':<10}")
        print("-" * 140)
        
        cursor.execute("""
            SELECT id, match_id, match_name, sport_name, market, status, bet_type, bet_timing
            FROM bets 
            ORDER BY created_at DESC
        """)
        
        bets = cursor.fetchall()
        
        for bet_id, match_id, match_name, sport_name, market, status, bet_type, bet_timing in bets:
            sport_display = sport_name if sport_name else "NULL"
            market_display = market if market else "NULL"
            timing_display = bet_timing if bet_timing else "NULL"
            print(f"{bet_id:<4} {match_id:<8} {match_name:<30} {sport_display:<10} {market_display:<15} {status:<10} {bet_type:<8} {timing_display:<10}")
        
        # Show summary by sport
        print("\n📊 SUMMARY BY SPORT:")
        print("=" * 50)
        cursor.execute("""
            SELECT sport_name, COUNT(*) as count
            FROM bets 
            GROUP BY sport_name
            ORDER BY count DESC
        """)
        
        sport_summary = cursor.fetchall()
        for sport_name, count in sport_summary:
            sport_display = sport_name if sport_name else "NULL"
            print(f"  {sport_display}: {count} bets")
        
        # Show summary by market
        print("\n📊 SUMMARY BY MARKET:")
        print("=" * 50)
        cursor.execute("""
            SELECT market, COUNT(*) as count
            FROM bets 
            GROUP BY market
            ORDER BY count DESC
        """)
        
        market_summary = cursor.fetchall()
        for market, count in market_summary:
            market_display = market if market else "NULL"
            print(f"  {market_display}: {count} bets")
        
        # Show pending bets by sport
        print("\n⏳ PENDING BETS BY SPORT:")
        print("=" * 50)
        cursor.execute("""
            SELECT sport_name, COUNT(*) as count
            FROM bets 
            WHERE status = 'pending'
            GROUP BY sport_name
            ORDER BY count DESC
        """)
        
        pending_summary = cursor.fetchall()
        for sport_name, count in pending_summary:
            sport_display = sport_name if sport_name else "NULL"
            print(f"  {sport_display}: {count} pending bets")
        
        # Show pending bets by market
        print("\n⏳ PENDING BETS BY MARKET:")
        print("=" * 50)
        cursor.execute("""
            SELECT market, COUNT(*) as count
            FROM bets 
            WHERE status = 'pending'
            GROUP BY market
            ORDER BY count DESC
        """)
        
        pending_market_summary = cursor.fetchall()
        for market, count in pending_market_summary:
            market_display = market if market else "NULL"
            print(f"  {market_display}: {count} pending bets")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 QUERYING BETS TABLE")
    print("=" * 50)
    query_bets_table()
