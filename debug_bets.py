#!/usr/bin/env python3
import sqlite3
import os

def check_db():
    db_path = os.path.join('src', 'database', 'app.db')
    print(f'Checking database at: {db_path}')
    print(f'File exists: {os.path.exists(db_path)}')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if bets table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bets'")
        bets_table_exists = cursor.fetchone() is not None
        print(f'Bets table exists: {bets_table_exists}')
        
        if bets_table_exists:
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
                # Added logic to infer sport for better debugging context
                match_name = bet[1]
                sport = "Unknown"
                if any(team in match_name.lower() for team in ['marines', 'hawks', 'dragons', 'tigers', 'eagles', 'buffaloes', 'giants', 'swallows', 'carp', 'baystars', 'lions', 'fighters', 'orix']):
                    sport = "Baseball"
                elif any(team in match_name.lower() for team in ['lakers', 'warriors', 'celtics', 'bulls', 'heat', 'knicks', 'nets', 'raptors', 'mavericks', 'rockets', 'spurs', 'thunder']):
                    sport = "Basketball"
                elif any(team in match_name.lower() for team in ['united', 'city', 'arsenal', 'chelsea', 'liverpool', 'barcelona', 'real madrid', 'bayern', 'psg', 'juventus', 'milan', 'inter']):
                    sport = "Soccer"
                elif any(team in match_name.lower() for team in ['patriots', 'cowboys', 'packers', 'steelers', '49ers', 'chiefs', 'bills', 'ravens', 'eagles', 'giants', 'jets']):
                    sport = "American Football"
                
                print(f'  ID: {bet[0]}, Match: {bet[1]}, Sport: {sport}, Match ID: {bet[2]}, Type: {bet[3]}, Stake: {bet[5]}, Odds: {bet[6]}, Return: {bet[7]}, Created: {bet[8]}')
        else:
            print('Bets table does not exist!')
        
        conn.close()
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    check_db()
