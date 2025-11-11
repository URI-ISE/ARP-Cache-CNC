#!/usr/bin/env python3
"""
Smoke test for Doom-and-Gloom Dashboard
Tests that all endpoints are responding correctly
"""

import requests
import sys
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(url, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == expected_status:
            print(f"✓ {method} {url} - Status {response.status_code}")
            return True
        else:
            print(f"✗ {method} {url} - Expected {expected_status}, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ {method} {url} - Error: {e}")
        return False

def main():
    print("🧪 Running Doom-and-Gloom Dashboard Smoke Tests\n")
    
    tests = [
        # Flask routes
        ("GET", f"{BASE_URL}/", None, 200),
        ("GET", f"{BASE_URL}/api/status", None, 200),
        ("GET", f"{BASE_URL}/api/iptables/status", None, 200),
        ("GET", f"{BASE_URL}/api/network/config", None, 200),
        
        # Dash routes
        ("GET", f"{BASE_URL}/dash/", None, 200),
        ("GET", f"{BASE_URL}/dash/_dash-dependencies", None, 200),
    ]
    
    passed = 0
    failed = 0
    
    for method, url, data, expected in tests:
        if test_endpoint(url, method, data, expected):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    # Test API response structure
    print("\n📊 Testing API Response Structure...")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        data = response.json()
        
        required_keys = ['connected', 'iptables_active', 'network_config', 
                        'statistics', 'active_attacks']
        
        missing = [key for key in required_keys if key not in data]
        if missing:
            print(f"✗ Missing keys in /api/status: {missing}")
            failed += 1
        else:
            print(f"✓ All required keys present in /api/status")
            print(f"  - Connected: {data['connected']}")
            print(f"  - IPTables Active: {data['iptables_active']}")
            print(f"  - CNC IP: {data['network_config']['cnc_ip']}")
            passed += 1
    except Exception as e:
        print(f"✗ Error testing API structure: {e}")
        failed += 1
    
    print(f"\n{'='*50}")
    print(f"Final: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")
    
    if failed == 0:
        print("✅ All smoke tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
