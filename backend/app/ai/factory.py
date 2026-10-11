import logging

from app.ai.base import AIProvider
from app.config import Settings
from app.errors import ServiceUnavailableError

logger = logging.getLogger("gamecraft")


def build_provider(settings: Settings) -> AIProvider:
    choice = settings.ai_provider
    if choice == "auto":
        if settings.cf_account_id and settings.cf_api_token:
            choice = "cloudflare"
        elif settings.gemini_api_key:
            choice = "gemini"
        else:
            choice = "mock"
        if choice == "mock" and settings.environment == "production":
            raise ServiceUnavailableError("Production requires an AI provider key (Cloudflare or Gemini).")

    if choice == "cloudflare":
        from app.ai.cloudflare import CloudflareProvider

        return CloudflareProvider(settings)

    if choice == "gemini":
        from app.ai.gemini import GeminiProvider

        return GeminiProvider(settings)

    from app.ai.mock import MockProvider

    logger.warning("Using the offline MOCK AI provider - images are placeholders.")
    return MockProvider()
