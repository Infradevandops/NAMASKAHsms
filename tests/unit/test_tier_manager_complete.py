"""Unit tests for tier manager service"""
import pytest
from app.services.tier_manager import TierManager
from app.models.user import User

@pytest.fixture
def tier_manager():
    return TierManager()

def test_get_tier_features_freemium(tier_manager):
    """Test freemium tier features"""
    features = tier_manager.get_tier_features('freemium')
    assert features['api_access'] == False
    assert features['area_code_filter'] == False
    assert features['isp_filter'] == False

def test_get_tier_features_payg(tier_manager):
    """Test PAYG tier features"""
    features = tier_manager.get_tier_features('payg')
    assert features['api_access'] == False
    assert features['area_code_filter'] == True
    assert features['isp_filter'] == True

def test_get_tier_features_pro(tier_manager):
    """Test Pro tier features"""
    features = tier_manager.get_tier_features('pro')
    assert features['api_access'] == True
    assert features['api_key_limit'] == 10
    assert features['affiliate_program'] == True

def test_check_feature_access(tier_manager):
    """Test feature access checking"""
    assert tier_manager.check_feature_access('freemium', 'api_access') == False
    assert tier_manager.check_feature_access('pro', 'api_access') == True
    assert tier_manager.check_feature_access('payg', 'area_code_filter') == True

def test_get_tier_pricing(tier_manager):
    """Test tier pricing calculation"""
    pricing = tier_manager.get_tier_pricing('freemium')
    assert pricing['monthly_fee'] == 0
    assert pricing['sms_rate'] > 0
    
    pricing_pro = tier_manager.get_tier_pricing('pro')
    assert pricing_pro['monthly_fee'] == 25
    assert pricing_pro['monthly_quota'] == 15

def test_can_upgrade_tier(tier_manager):
    """Test tier upgrade validation"""
    assert tier_manager.can_upgrade('freemium', 'payg') == True
    assert tier_manager.can_upgrade('pro', 'freemium') == False
    assert tier_manager.can_upgrade('custom', 'pro') == False
