"""Translation service stub — i18n support placeholder."""

SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "zh", "ja", "ar", "hi", "yo"]


class TranslationService:
    """Minimal translation service. Full i18n implementation deferred."""

    def __init__(self, language: str = "en"):
        self.language = language if language in SUPPORTED_LANGUAGES else "en"

    def get_available_languages(self) -> list:
        return SUPPORTED_LANGUAGES

    def translate(self, key: str, **kwargs) -> str:
        """Return key as-is (no translations loaded yet)."""
        result = key
        for k, v in kwargs.items():
            result = result.replace(f"{{{k}}}", str(v))
        return result
