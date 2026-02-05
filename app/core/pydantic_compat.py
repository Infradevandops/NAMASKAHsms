"""Pydantic compatibility layer for v1/v2 support."""

try:
    # Try Pydantic v2 first
    from pydantic import field_validator, Field, BaseModel
    from pydantic_settings import BaseSettings
    
    PYDANTIC_V2 = True
    
except ImportError:
    try:
        # Pydantic v1 fallback
        from pydantic import validator, Field, BaseModel, BaseSettings

        PYDANTIC_V2 = False

        # Create a compatibility wrapper for field_validator
        def field_validator(*args, **kwargs):
            """Compatibility wrapper for Pydantic v1 validator."""
            # Remove v2-specific arguments that don't exist in v1
            v1_kwargs = {k: v for k, v in kwargs.items() if k not in ["mode"]}
            return validator(*args, **v1_kwargs)

    except ImportError:
        raise ImportError("Neither Pydantic v1 nor v2 could be imported")