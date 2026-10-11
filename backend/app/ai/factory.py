import logging

from app.ai.base import AIProvider
from app.config import Settings
from app.errors import ServiceUnavailableError

logger = logging.getLogger("gamecraft")


def build_provider(settings: Settings) -> AIProvider:
    choice = settings.ai_provider
    if choice == "auto":
        choice = "gemini" if settings.gemini_api_key else "mock"
        if choice == "mock" and settings.environment == "production":
            raise ServiceUnavailableError("Production requires GEMINI_API_KEY (or AI_PROVIDER=gemini).")

    if choice == "gemini":
        from app.ai.gemini import GeminiProvider

        return GeminiProvider(settings)

    from app.ai.mock import MockProvider

    logger.warning("Using the offline MOCK AI provider - images are placeholders.")
    return MockProvider()
