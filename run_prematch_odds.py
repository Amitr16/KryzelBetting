#!/usr/bin/env python3
"""
Standalone Pre-Match Odds Service Runner
"""

import sys
import os
import time
import signal
import argparse
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.prematch_odds_service import get_prematch_odds_service

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    service = get_prematch_odds_service()
    service.stop()
    print("✅ Service stopped. Goodbye!")
    sys.exit(0)

def main():
    """Main function to run the pre-match odds service"""
    parser = argparse.ArgumentParser(description='GoalServe Pre-Match Odds Service')
    parser.add_argument('--folder', '-f', 
                       default="Sports Pre Match",
                       help='Base folder for storing odds files')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Run a test fetch and exit')
    parser.add_argument('--once', '-o', action='store_true',
                       help='Fetch once and exit')
    parser.add_argument('--sport', '-s', 
                       help='Fetch only a specific sport (for --once mode)')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🎯 GoalServe Pre-Match Odds Service")
    print("=" * 50)
    print(f"📁 Base folder: {args.folder}")
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Get the service instance
        service = get_prematch_odds_service()
        
        # Handle relative paths - make them relative to the script location
        if not os.path.isabs(args.folder):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            args.folder = os.path.join(script_dir, args.folder)
        
        # Update base folder if specified
        if args.folder != str(service.base_folder):
            service.base_folder = Path(args.folder)
            service._ensure_folder_structure()
        
        if args.test:
            print("🧪 Running test mode...")
            print("Testing service configuration...")
            
            stats = service.get_stats()
            print(f"✅ Total sports configured: {stats['total_sports']}")
            print(f"✅ Base folder: {stats['base_folder']}")
            
            # Test URL building
            date_start, date_end = service._get_dynamic_dates()
            print(f"✅ Date range: {date_start} to {date_end}")
            
            # Test single sport fetch
            print("\n🔄 Testing soccer odds fetch...")
            success = service._fetch_single_sport_odds('soccer')
            if success:
                print("✅ Soccer odds fetched successfully")
                
                # Check files
                files = service.get_recent_files(sport_name='soccer', limit=3)
                if files:
                    print(f"✅ Found {len(files)} soccer files")
                    for file in files[:2]:
                        print(f"   📄 {file['filename']} ({file['size']} bytes)")
                else:
                    print("❌ No soccer files found")
            else:
                print("❌ Soccer odds fetch failed")
            
            print("\n✅ Test completed!")
            return
        
        if args.once:
            print("🔄 Running single fetch mode...")
            
            if args.sport:
                print(f"🎯 Fetching odds for {args.sport}...")
                if args.sport not in service.sports_config:
                    print(f"❌ Unknown sport: {args.sport}")
                    print(f"Available sports: {', '.join(service.sports_config.keys())}")
                    return
                
                success = service._fetch_single_sport_odds(args.sport)
                if success:
                    print(f"✅ Successfully fetched {args.sport} odds")
                else:
                    print(f"❌ Failed to fetch {args.sport} odds")
            else:
                print("🔄 Fetching odds for all sports...")
                service._fetch_all_sports_odds()
                print("✅ All sports fetch completed")
            
            # Show summary
            files = service.get_recent_files(limit=10)
            print(f"\n📊 Summary: {len(files)} files created")
            
            files_by_sport = {}
            for file in files:
                sport = file['sport']
                if sport not in files_by_sport:
                    files_by_sport[sport] = 0
                files_by_sport[sport] += 1
            
            for sport, count in sorted(files_by_sport.items()):
                print(f"   {sport}: {count} files")
            
            return
        
        # Continuous mode
        print("🚀 Starting continuous pre-match odds service...")
        print("   • Fetch interval: 30 seconds")
        print("   • Single attempt per sport (no retries)")
        print("   • Date range: Yesterday to Tomorrow")
        print()
        
        # Start the service
        if service.start():
            print("✅ Service started successfully!")
            print("📊 Service statistics:")
            stats = service.get_stats()
            print(f"   • Total sports: {stats['total_sports']}")
            print(f"   • Base folder: {stats['base_folder']}")
            print(f"   • Service running: {stats['service_running']}")
            print()
            print("🔄 Service is now running...")
            print("Press Ctrl+C to stop the service")
            print()
            
            # Keep the main thread alive
            try:
                while service.running:
                    time.sleep(1)
                    
                    # Print periodic status updates
                    if int(time.time()) % 60 == 0:  # Every minute
                        current_stats = service.get_stats()
                        print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] "
                              f"Successful: {current_stats['stats']['successful_fetches']}, "
                              f"Failed: {current_stats['stats']['failed_fetches']}")
            
            except KeyboardInterrupt:
                print("\n🛑 Keyboard interrupt received...")
                service.stop()
                print("✅ Service stopped gracefully")
        
        else:
            print("❌ Failed to start service")
            return 1
            
    except Exception as e:
        print(f"❌ Error running service: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
