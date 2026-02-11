#!/usr/bin/env python3
"""Test all sidebar tabs and their functionality"""

import requests
import sys
from typing import Dict, List

BASE_URL = "http://localhost:8001"

# Sidebar tabs configuration
SIDEBAR_TABS = {
    "Main": [
        {"name": "Dashboard", "url": "/dashboard", "tier": "freemium", "icon": "📊"},
    ],
    "Services": [
        {"name": "SMS Verification", "url": "/verify", "tier": "freemium", "icon": "📱"},
        {"name": "Voice Verification", "url": "/voice-verify", "tier": "payg", "icon": "📞"},
    ],
    "Finance": [
        {"name": "Wallet", "url": "/wallet", "tier": "freemium", "icon": "💰"},
        {"name": "History", "url": "/history", "tier": "freemium", "icon": "📜"},
        {"name": "Bulk Purchase", "url": "/bulk-purchase", "tier": "pro", "icon": "📦"},
    ],
    "Developers": [
        {"name": "API Keys", "url": "/settings?tab=api-keys", "tier": "payg", "icon": "🔑"},
        {"name": "Webhooks", "url": "/webhooks", "tier": "payg", "icon": "🔗"},
        {"name": "API Docs", "url": "/api-docs", "tier": "payg", "icon": "📚"},
    ],
    "General": [
        {"name": "Analytics", "url": "/analytics", "tier": "freemium", "icon": "📈"},
        {"name": "Pricing", "url": "/pricing", "tier": "freemium", "icon": "💳"},
        {"name": "Referral Program", "url": "/referrals", "tier": "payg", "icon": "🤝"},
        {"name": "Notifications", "url": "/notifications", "tier": "freemium", "icon": "🔔"},
        {"name": "Settings", "url": "/settings", "tier": "freemium", "icon": "⚙️"},
    ],
    "Footer": [
        {"name": "Privacy Settings", "url": "/privacy-settings", "tier": "freemium", "icon": "🔒"},
    ]
}

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@namaskah.app", "password": "Namaskah@Admin2024"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"❌ Failed to get auth token: {e}")
    return None

def test_tab(tab: Dict, token: str = None) -> Dict:
    """Test a single tab"""
    result = {
        "name": tab["name"],
        "url": tab["url"],
        "tier": tab["tier"],
        "status": "unknown",
        "status_code": None,
        "error": None
    }
    
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        response = requests.get(
            f"{BASE_URL}{tab['url']}",
            headers=headers,
            timeout=5,
            allow_redirects=False
        )
        
        result["status_code"] = response.status_code
        
        if response.status_code == 200:
            result["status"] = "✅ Working"
        elif response.status_code == 302:
            result["status"] = "🔄 Redirect"
        elif response.status_code == 404:
            result["status"] = "❌ Not Found"
        elif response.status_code == 401:
            result["status"] = "🔐 Auth Required"
        elif response.status_code == 403:
            result["status"] = "🚫 Forbidden"
        else:
            result["status"] = f"⚠️  Status {response.status_code}"
            
    except requests.exceptions.Timeout:
        result["status"] = "⏱️  Timeout"
        result["error"] = "Request timeout"
    except requests.exceptions.ConnectionError:
        result["status"] = "🔌 Connection Error"
        result["error"] = "Cannot connect to server"
    except Exception as e:
        result["status"] = "❌ Error"
        result["error"] = str(e)
    
    return result

def print_section_results(section: str, tabs: List[Dict], results: List[Dict]):
    """Print results for a section"""
    print(f"\n{'='*70}")
    print(f"  {section}")
    print(f"{'='*70}")
    
    for tab, result in zip(tabs, results):
        tier_badge = f"[{result['tier'].upper()}]"
        print(f"{tab['icon']}  {result['name']:<25} {tier_badge:<12} {result['status']}")
        if result['error']:
            print(f"    └─ Error: {result['error']}")

def main():
    print("="*70)
    print("  SIDEBAR TABS FUNCTIONALITY TEST")
    print("="*70)
    print(f"\nTesting against: {BASE_URL}")
    
    # Get auth token
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    if token:
        print("✅ Authentication successful")
    else:
        print("⚠️  Authentication failed - testing without auth")
    
    # Test all tabs
    all_results = {}
    total_tabs = 0
    working_tabs = 0
    
    for section, tabs in SIDEBAR_TABS.items():
        results = []
        for tab in tabs:
            result = test_tab(tab, token)
            results.append(result)
            total_tabs += 1
            if "✅" in result["status"]:
                working_tabs += 1
        
        all_results[section] = results
        print_section_results(section, tabs, results)
    
    # Summary
    print(f"\n{'='*70}")
    print("  SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tabs: {total_tabs}")
    print(f"Working: {working_tabs} ✅")
    print(f"Issues: {total_tabs - working_tabs} ❌")
    print(f"Success Rate: {(working_tabs/total_tabs*100):.1f}%")
    
    # Detailed breakdown
    print(f"\n{'='*70}")
    print("  STATUS BREAKDOWN")
    print(f"{'='*70}")
    
    status_counts = {}
    for section_results in all_results.values():
        for result in section_results:
            status = result["status"].split()[0]  # Get emoji/status
            status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{status} {count} tabs")
    
    # Tier breakdown
    print(f"\n{'='*70}")
    print("  TIER BREAKDOWN")
    print(f"{'='*70}")
    
    tier_stats = {"freemium": {"total": 0, "working": 0},
                  "payg": {"total": 0, "working": 0},
                  "pro": {"total": 0, "working": 0}}
    
    for section_results in all_results.values():
        for result in section_results:
            tier = result["tier"]
            if tier in tier_stats:
                tier_stats[tier]["total"] += 1
                if "✅" in result["status"]:
                    tier_stats[tier]["working"] += 1
    
    for tier, stats in tier_stats.items():
        if stats["total"] > 0:
            rate = (stats["working"]/stats["total"]*100)
            print(f"{tier.upper():<12} {stats['working']}/{stats['total']} working ({rate:.0f}%)")
    
    print(f"\n{'='*70}\n")
    
    # Exit code
    if working_tabs == total_tabs:
        print("✅ ALL TABS WORKING")
        return 0
    elif working_tabs > total_tabs * 0.7:
        print("⚠️  MOST TABS WORKING (>70%)")
        return 0
    else:
        print("❌ MANY TABS FAILING (<70%)")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
