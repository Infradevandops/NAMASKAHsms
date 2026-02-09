"""Expanded unit tests for SMS service"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.textverified_service import TextVerifiedService

class TestSMSServiceExpanded:
    
    @pytest.fixture
    def sms_service(self):
        return TextVerifiedService()
    
    def test_purchase_number_success(self, sms_service):
        """Test successful number purchase"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.return_value = {
                'success': True,
                'number': '+12345678901',
                'id': 'test_id_123'
            }
            
            result = sms_service.purchase_number('telegram', 'US')
            assert result['success'] == True
            assert 'number' in result
    
    def test_purchase_number_failure(self, sms_service):
        """Test failed number purchase"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.return_value = {'success': False, 'error': 'No numbers available'}
            
            result = sms_service.purchase_number('telegram', 'US')
            assert result['success'] == False
    
    def test_get_sms_code_success(self, sms_service):
        """Test retrieving SMS code"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.return_value = {
                'success': True,
                'sms_code': '123456',
                'message': 'Your code is 123456'
            }
            
            result = sms_service.get_sms('test_id_123')
            assert result['success'] == True
            assert result['sms_code'] == '123456'
    
    def test_get_sms_code_pending(self, sms_service):
        """Test SMS code still pending"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.return_value = {'success': False, 'status': 'pending'}
            
            result = sms_service.get_sms('test_id_123')
            assert result['success'] == False
    
    def test_cancel_verification(self, sms_service):
        """Test canceling verification"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.return_value = {'success': True}
            
            result = sms_service.cancel_verification('test_id_123')
            assert result['success'] == True
    
    def test_get_available_services(self, sms_service):
        """Test getting available services"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.return_value = {
                'success': True,
                'services': ['telegram', 'whatsapp', 'discord']
            }
            
            result = sms_service.get_services()
            assert len(result['services']) > 0
    
    def test_get_balance(self, sms_service):
        """Test getting account balance"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.return_value = {'success': True, 'balance': 100.50}
            
            result = sms_service.get_balance()
            assert result['balance'] > 0
    
    def test_invalid_service_name(self, sms_service):
        """Test purchase with invalid service"""
        result = sms_service.purchase_number('', 'US')
        assert result['success'] == False
    
    def test_invalid_country_code(self, sms_service):
        """Test purchase with invalid country"""
        result = sms_service.purchase_number('telegram', '')
        assert result['success'] == False
    
    def test_api_timeout(self, sms_service):
        """Test API timeout handling"""
        with patch.object(sms_service, '_make_request') as mock_request:
            mock_request.side_effect = TimeoutError()
            
            result = sms_service.purchase_number('telegram', 'US')
            assert result['success'] == False
