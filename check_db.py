#!/usr/bin/env python3

import sqlite3
import os

def check_db():
    db_path = 'src/database/app.db'
    print(f'Checking database at: {db_path}')
    print(f'File exists: {os.path.exists(db_path)}')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check total bets
        cursor.execute("SELECT COUNT(*) FROM bets")
        total_count = cursor.fetchone()[0]
        print(f'Total bets: {total_count}')
        
        # Check pending bets
        cursor.execute("SELECT COUNT(*) FROM bets WHERE status = 'pending'")
        pending_count = cursor.fetchone()[0]
        print(f'Pending bets: {pending_count}')
        
        # Get pending bets with all details
        cursor.execute("""
            SELECT id, match_name, match_id, bet_type, status, stake, odds, potential_return, created_at 
            FROM bets 
            WHERE status = 'pending' 
            ORDER BY created_at DESC
        """)
        pending_bets = cursor.fetchall()
        print('\nPending bets details:')
        for bet in pending_bets:
            # Try to determine sport from match name
            match_name = bet[1]
            sport = "Unknown"
            if "Marines" in match_name or "Hawks" in match_name or "Dragons" in match_name or "Tigers" in match_name or "Eagles" in match_name or "Buffaloes" in match_name:
                sport = "Baseball"
            elif "vs" in match_name and ("vs" in match_name.lower()):
                sport = "Soccer"
            
            print(f'  ID: {bet[0]}, Match: {bet[1]}, Sport: {sport}, Match ID: {bet[2]}, Type: {bet[3]}, Stake: {bet[5]}, Odds: {bet[6]}, Return: {bet[7]}, Created: {bet[8]}')
        
        conn.close()
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    check_db()
