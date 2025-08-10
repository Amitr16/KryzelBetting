#!/usr/bin/env python3
"""
Test script for the pre-match odds service
"""

import sys
import os
import time
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.prematch_odds_service import get_prematch_odds_service

def test_prematch_odds_service():
    """Test the pre-match odds service"""
    print("🧪 Testing Pre-Match Odds Service")
    print("=" * 50)
    
    try:
        # Get the service instance
        service = get_prematch_odds_service()
        
        # Test 1: Check service configuration
        print("\n1️⃣ Testing service configuration...")
        stats = service.get_stats()
        print(f"   ✅ Service running: {stats['service_running']}")
        print(f"   ✅ Total sports: {stats['total_sports']}")
        print(f"   ✅ Base folder: {stats['base_folder']}")
        print(f"   ✅ Sports configured: {', '.join(stats['sports_configured'][:5])}...")
        
        # Test 2: Test URL building
        print("\n2️⃣ Testing URL building...")
        date_start, date_end = service._get_dynamic_dates()
        print(f"   ✅ Date range: {date_start} to {date_end}")
        
        # Test URL for soccer
        soccer_url = service._build_odds_url('soccer', date_start, date_end)
        print(f"   ✅ Soccer URL: {soccer_url}")
        
        # Test 3: Test single sport fetch
        print("\n3️⃣ Testing single sport fetch (soccer)...")
        success = service._fetch_single_sport_odds('soccer')
        if success:
            print("   ✅ Soccer odds fetched successfully")
        else:
            print("   ❌ Soccer odds fetch failed")
        
        # Test 4: Check if files were created
        print("\n4️⃣ Checking created files...")
        files = service.get_recent_files(sport_name='soccer', limit=3)
        if files:
            print(f"   ✅ Found {len(files)} soccer files")
            for file in files[:2]:  # Show first 2 files
                print(f"      📄 {file['filename']} ({file['size']} bytes)")
        else:
            print("   ❌ No soccer files found")
        
        # Test 5: Test service start/stop
        print("\n5️⃣ Testing service start/stop...")
        
        # Start the service
        if service.start():
            print("   ✅ Service started successfully")
            
            # Let it run for a few seconds
            print("   ⏳ Running service for 10 seconds...")
            time.sleep(10)
            
            # Stop the service
            service.stop()
            print("   ✅ Service stopped successfully")
        else:
            print("   ❌ Failed to start service")
        
        # Test 6: Test all sports fetch
        print("\n6️⃣ Testing all sports fetch...")
        service._fetch_all_sports_odds()
        print("   ✅ All sports fetch completed")
        
        # Test 7: Check all files
        print("\n7️⃣ Checking all created files...")
        all_files = service.get_recent_files(limit=10)
        print(f"   ✅ Total files found: {len(all_files)}")
        
        # Group by sport
        files_by_sport = {}
        for file in all_files:
            sport = file['sport']
            if sport not in files_by_sport:
                files_by_sport[sport] = 0
            files_by_sport[sport] += 1
        
        print("   📊 Files by sport:")
        for sport, count in sorted(files_by_sport.items()):
            print(f"      {sport}: {count} files")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "http://localhost:5000/api/prematch-odds"
        
        # Test 1: Get status
        print("\n1️⃣ Testing status endpoint...")
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('service_running', 'Unknown')}")
            print(f"   ✅ Total sports: {data.get('total_sports', 'Unknown')}")
        else:
            print(f"   ❌ Status request failed: {response.status_code}")
        
        # Test 2: Get sports list
        print("\n2️⃣ Testing sports endpoint...")
        response = requests.get(f"{base_url}/sports")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Sports count: {data.get('total_sports', 'Unknown')}")
            sports = data.get('sports', [])
            for sport in sports[:3]:  # Show first 3
                print(f"      {sport['icon']} {sport['display_name']} ({sport['name']})")
        else:
            print(f"   ❌ Sports request failed: {response.status_code}")
        
        # Test 3: Test URL endpoint
        print("\n3️⃣ Testing URL test endpoint...")
        response = requests.get(f"{base_url}/test-url/soccer")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Soccer URL: {data.get('url', 'Unknown')}")
        else:
            print(f"   ❌ URL test failed: {response.status_code}")
        
        # Test 4: Get recent files
        print("\n4️⃣ Testing files endpoint...")
        response = requests.get(f"{base_url}/files?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Files count: {data.get('total_files', 'Unknown')}")
        else:
            print(f"   ❌ Files request failed: {response.status_code}")
        
        print("\n✅ API endpoint tests completed!")
        
    except Exception as e:
        print(f"\n❌ API test failed with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Pre-Match Odds Service Tests")
    print("=" * 60)
    
    # Test the service directly
    service_success = test_prematch_odds_service()
    
    # Test API endpoints (if server is running)
    print("\n" + "=" * 60)
    api_success = test_api_endpoints()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Service Tests: {'✅ PASSED' if service_success else '❌ FAILED'}")
    print(f"   API Tests: {'✅ PASSED' if api_success else '❌ FAILED'}")
    
    if service_success and api_success:
        print("\n🎉 All tests passed! The pre-match odds service is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the logs above.")
