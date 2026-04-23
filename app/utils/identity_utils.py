"""Identity formatting utilities for admin privacy and clarity."""

import hashlib
from typing import Optional

def format_admin_identity(user_email: str, google_id: Optional[str] = None, internal_id: Optional[str] = None) -> str:
    """
    Format user identity for admin display according to institutional rules:
    1. Show Email (Primary)
    2. Show Google ID if available
    3. Generate/Show a 6-8 digit obfuscated UserID for internal tracking.
    """
    # 1. Masked/Obfuscated 6-8 digit UserID
    # We use a hash of the internal UUID or email to generate a stable 6-8 digit numeric ID
    seed = internal_id or user_email
    hash_obj = hashlib.sha256(seed.encode())
    numeric_id = int(hash_obj.hexdigest(), 16) % 100000000 # 8 digits max
    if numeric_id < 100000: numeric_id += 100000 # Ensure at least 6 digits
    
    id_str = f"ID-{numeric_id}"
    
    # 2. Combine with email and google_id
    display_name = f"{user_email} ({id_str})"
    
    if google_id:
        display_name = f"{display_name} [G:{google_id[:8]}...]"
        
    return display_name

def get_short_id(internal_id: str) -> str:
    """Generate a stable 6-digit identification for UI tables."""
    hash_obj = hashlib.sha256(internal_id.encode())
    numeric_id = int(hash_obj.hexdigest(), 16) % 1000000
    return f"{numeric_id:06d}"
