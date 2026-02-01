"""Translation service for multi-language support."""


import json
from pathlib import Path

class TranslationService:

    """Handle translations for multiple languages."""

def __init__(self, language: str = "en"):

        self.language = language
        self.translations = self._load_translations()

def _load_translations(self) -> dict:

        """Load translation file for language."""
try:
            path = Path(__file__).parent.parent / "translations" / self.language / "messages.json"
with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
except FileNotFoundError:
            return {}

def translate(self, key: str, **kwargs) -> str:

        """Get translated text by key."""
        keys = key.split(".")
        value = self.translations

for k in keys:
if isinstance(value, dict):
                value = value.get(k, key)
else:
                return key

if isinstance(value, str) and kwargs:
            return value.format(**kwargs)

        return str(value) if value else key

def get_available_languages(self) -> list:

        """List supported languages."""
        return ["en", "es", "fr", "de", "pt", "zh", "ja", "ar", "hi", "yo"]