"""
i18n Utilities for Server-Side Translation Support
"""
import json
from pathlib import Path
from typing import Dict, Any

# Cache translations in memory
_translations_cache: Dict[str, Dict[str, Any]] = {}


def load_translations(locale: str = "en") -> Dict[str, Any]:
    """
    Load translations from JSON file.
    
    Args:
        locale: Language code (en, es, fr, etc.)
        
    Returns:
        Dictionary of translations
    """
    # Check cache first
    if locale in _translations_cache:
        return _translations_cache[locale]
    
    # Load from file
    translations_file = Path(__file__).parent.parent.parent / "static" / "locales" / f"{locale}.json"
    
    if not translations_file.exists():
        # Fallback to English
        if locale != "en":
            return load_translations("en")
        return {}
    
    try:
        with open(translations_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
            _translations_cache[locale] = translations
            return translations
    except Exception as e:
        print(f"[i18n] Failed to load {locale}.json: {e}")
        if locale != "en":
            return load_translations("en")
        return {}


def get_translations_for_template(locale: str = "en") -> str:
    """
    Get translations as JSON string for embedding in HTML.
    
    Args:
        locale: Language code
        
    Returns:
        JSON string of translations
    """
    translations = load_translations(locale)
    return json.dumps(translations)


def clear_cache():
    """Clear the translations cache."""
    global _translations_cache
    _translations_cache = {}
