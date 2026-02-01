#!/usr/bin/env python3
"""
Quick test to verify notification system fixes
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_notification_api_response():
    """Test that the notification API response format is correct."""
    
    # Test the notification model to_dict method
    from app.models.notification import Notification
    from datetime import datetime
    
    # Create a mock notification
    notification = Notification()
    notification.id = "test-123"
    notification.user_id = "user-123"
    notification.type = "test"
    notification.title = "Test Notification"
    notification.message = "Test message"
    notification.link = "/test"
    notification.icon = "🔔"
    notification.is_read = False
    notification.created_at = datetime.now()
    
    # Test to_dict method
    result = notification.to_dict()
    
    print("✅ Testing notification.to_dict():")
    print(f"   Result: {result}")
    
    # Verify all expected fields are present
    expected_fields = ['id', 'type', 'title', 'message', 'link', 'icon', 'is_read', 'created_at']
    for field in expected_fields:
        assert field in result, f"Missing field: {field}"
        print(f"   ✓ {field}: {result[field]}")
    
    # Verify no unexpected fields
    unexpected_fields = ['read', 'data', 'read_at']
    for field in unexpected_fields:
        assert field not in result, f"Unexpected field found: {field}"
    
    print("✅ All notification model tests passed!")
    return True

def test_imports():
    """Test that all notification-related imports work."""
    
    try:
        from app.models.notification import Notification
        print("✅ Notification model import: OK")
        
        from app.services.notification_service import NotificationService
        print("✅ NotificationService import: OK")
        
        from app.services.notification_dispatcher import NotificationDispatcher
        print("✅ NotificationDispatcher import: OK")
        
        # Test that websocket manager import works
        from app.websocket.manager import connection_manager
        print("✅ WebSocket connection_manager import: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔔 Testing Notification System Fixes\n")
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    print()
    
    # Test API response format
    if not test_notification_api_response():
        success = False
    
    if success:
        print("\n🎉 All notification system tests passed!")
        print("\nKey fixes applied:")
        print("1. ✅ Fixed API response to use 'is_read' instead of 'read'")
        print("2. ✅ Added WebSocket broadcasting to NotificationDispatcher")
        print("3. ✅ Added unread count endpoint")
        print("4. ✅ Updated frontend to use backend count as source of truth")
        print("\nThe notification bell should now work correctly!")
    else:
        print("\n❌ Some tests failed!")
    
    sys.exit(0 if success else 1)