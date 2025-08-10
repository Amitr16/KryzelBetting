#!/usr/bin/env python3
"""
Update sport_name column for specific bets shown in the image
"""

import sqlite3
import os
import json

def update_sport_names():
    """Update sport_name for specific bets based on the image"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            return False
        
        print(f"🔧 Updating sport_name for specific bets on: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if sport_name column exists
        cursor.execute("PRAGMA table_info(bets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sport_name' not in columns:
            print("❌ sport_name column not found - run migration first")
            conn.close()
            return False
        
        print("✅ sport_name column exists")
        
        # Update specific bets based on the image
        updates = [
            # Row 1: Forli vs Ancona
            {
                'match_name': 'Forli vs Ancona',
                'sport_name': 'soccer'
            },
            # Row 2: Combo Bet (2 selections) - both baseball teams
            {
                'match_name': 'Combo Bet (2 selections)',
                'sport_name': 'baseball'  # Both selections are baseball
            },
            # Row 3: Chiba Lotte Marines vs Fukuoka S. Hawks
            {
                'match_name': 'Chiba Lotte Marines vs Fukuoka S. Hawks',
                'sport_name': 'baseball'
            },
            # Row 4: Chunichi Dragons vs Hanshin Tigers
            {
                'match_name': 'Chunichi Dragons vs Hanshin Tigers',
                'sport_name': 'baseball'
            },
            # Row 5: Rakuten Gold. Eagles vs Orix Buffaloes
            {
                'match_name': 'Rakuten Gold. Eagles vs Orix Buffaloes',
                'sport_name': 'baseball'
            },
            # Row 6: Chunichi Dragons vs Hanshin Tigers (duplicate)
            {
                'match_name': 'Chunichi Dragons vs Hanshin Tigers',
                'sport_name': 'baseball'
            }
        ]
        
        updated_count = 0
        
        for update in updates:
            match_name = update['match_name']
            sport_name = update['sport_name']
            
            # Update all bets with this match name
            cursor.execute("""
                UPDATE bets 
                SET sport_name = ? 
                WHERE match_name = ?
            """, (sport_name, match_name))
            
            rows_affected = cursor.rowcount
            updated_count += rows_affected
            
            if rows_affected > 0:
                print(f"  ✅ {match_name} → {sport_name} ({rows_affected} bets updated)")
            else:
                print(f"  ⚠️  {match_name} → {sport_name} (no bets found)")
        
        conn.commit()
        print(f"\n✅ Updated {updated_count} total bets with sport_name")
        
        # Show current status
        print("\n📊 CURRENT SPORT NAMES:")
        print("=" * 50)
        
        cursor.execute("""
            SELECT match_name, sport_name, COUNT(*) as count
            FROM bets 
            GROUP BY match_name, sport_name
            ORDER BY match_name
        """)
        
        results = cursor.fetchall()
        for match_name, sport_name, count in results:
            print(f"  {match_name}: {sport_name or 'NULL'} ({count} bets)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return False

def show_combo_bet_details():
    """Show details of combo bets to verify sport names"""
    try:
        db_path = os.path.join('src', 'database', 'app.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🎯 COMBO BET DETAILS:")
        print("=" * 50)
        
        # Get combo bets
        cursor.execute("""
            SELECT id, match_name, combo_selections, sport_name
            FROM bets 
            WHERE bet_type = 'combo'
            ORDER BY created_at DESC
        """)
        
        combo_bets = cursor.fetchall()
        
        for bet_id, match_name, combo_selections, sport_name in combo_bets:
            print(f"\nCombo Bet ID: {bet_id}")
            print(f"Match Name: {match_name}")
            print(f"Sport Name: {sport_name or 'NULL'}")
            
            if combo_selections:
                try:
                    selections = json.loads(combo_selections)
                    print(f"Selections ({len(selections)}):")
                    for i, selection in enumerate(selections, 1):
                        match_name = selection.get('match_name', 'Unknown')
                        selection_name = selection.get('selection', 'Unknown')
                        print(f"  {i}. {match_name} - {selection_name}")
                except json.JSONDecodeError:
                    print("  ❌ Invalid combo_selections JSON")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to show combo bet details: {e}")
        return False

if __name__ == "__main__":
    print("🚀 UPDATING SPORT NAMES FOR SPECIFIC BETS")
    print("=" * 50)
    
    # Update sport names
    if update_sport_names():
        print("\n📋 COMBO BET VERIFICATION:")
        show_combo_bet_details()
        
        print("\n✅ Update completed successfully!")
        print("\n📝 Summary:")
        print("  - Forli vs Ancona → soccer")
        print("  - Combo Bet → baseball (both selections are baseball)")
        print("  - All other matches → baseball")
        print("  - Ready for settlement service to use stored sport_name")
    else:
        print("\n❌ Update failed!")
