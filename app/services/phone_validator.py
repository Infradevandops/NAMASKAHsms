"""
Phone Validator Service - VOIP/Landline Detection
Uses Google's libphonenumber for offline phone validation
"""
from typing import Dict, Optional
import logging

try:
    import phonenumbers
    from phonenumbers import NumberParseException, PhoneNumberType
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Known VOIP area codes (best-effort detection)
VOIP_AREA_CODES = {
    "747",  # Google Voice
    "463",  # Some VOIP providers
}


class PhoneValidator:
    """Validates phone numbers and detects VOIP/landline"""
    
    def __init__(self):
        if not PHONENUMBERS_AVAILABLE:
            logger.warning("phonenumbers library not available - validation disabled")
    
    def validate_mobile(self, phone_number: Optional[str], country_code: str = "US") -> Dict:
        """
        Validate if phone number is mobile (not VOIP/landline)
        
        Returns:
            {
                "is_valid": bool,
                "is_mobile": bool,
                "is_voip": bool,
                "number_type": str,
                "voip_risk": str,  # "low", "medium", "high"
                "error": str (optional)
            }
        """
        if not PHONENUMBERS_AVAILABLE:
            return {
                "is_valid": False,
                "is_mobile": False,
                "is_voip": False,
                "error": "phonenumbers library not available"
            }
        
        if not phone_number:
            return {
                "is_valid": False,
                "is_mobile": False,
                "is_voip": False,
                "error": "Phone number is required"
            }
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone_number, country_code)
            
            # Check if valid
            is_valid = phonenumbers.is_valid_number(parsed)
            
            # Get number type
            number_type = phonenumbers.number_type(parsed)
            type_name = self._get_type_name(number_type)
            
            # Check if mobile
            is_mobile = number_type in [
                PhoneNumberType.MOBILE,
                PhoneNumberType.FIXED_LINE_OR_MOBILE
            ]
            
            # VOIP detection (best-effort)
            is_voip, voip_risk = self._detect_voip(parsed, phone_number)
            
            return {
                "is_valid": is_valid,
                "is_mobile": is_mobile,
                "is_voip": is_voip,
                "number_type": type_name,
                "voip_risk": voip_risk
            }
            
        except NumberParseException as e:
            return {
                "is_valid": False,
                "is_mobile": False,
                "is_voip": False,
                "error": f"Invalid phone number: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Phone validation error: {e}")
            return {
                "is_valid": False,
                "is_mobile": False,
                "is_voip": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def _get_type_name(self, number_type: int) -> str:
        """Convert PhoneNumberType enum to string"""
        type_map = {
            PhoneNumberType.FIXED_LINE: "FIXED_LINE",
            PhoneNumberType.MOBILE: "MOBILE",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
            PhoneNumberType.TOLL_FREE: "TOLL_FREE",
            PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
            PhoneNumberType.SHARED_COST: "SHARED_COST",
            PhoneNumberType.VOIP: "VOIP",
            PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
            PhoneNumberType.PAGER: "PAGER",
            PhoneNumberType.UAN: "UAN",
            PhoneNumberType.VOICEMAIL: "VOICEMAIL",
            PhoneNumberType.UNKNOWN: "UNKNOWN"
        }
        return type_map.get(number_type, "UNKNOWN")
    
    def _detect_voip(self, parsed_number, original_number: str) -> tuple[bool, str]:
        """
        Best-effort VOIP detection
        Returns: (is_voip, risk_level)
        """
        # Check if phonenumbers library detected VOIP
        number_type = phonenumbers.number_type(parsed_number)
        if number_type == PhoneNumberType.VOIP:
            return True, "high"
        
        # Check known VOIP area codes
        if original_number:
            for voip_code in VOIP_AREA_CODES:
                if voip_code in original_number:
                    return True, "high"
        
        return False, "low"
