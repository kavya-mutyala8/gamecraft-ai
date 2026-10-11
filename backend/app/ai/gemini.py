"""Gemini provider (google-genai SDK).

The SDK is synchronous, so calls run in worker threads with a hard timeout.
Provider failures are mapped to typed AppErrors; raw provider text is only logged.
"""

import asyncio
import json
import logging
import re
from typing import Any, Callable, TypeVar

from pydantic import ValidationError

from app.ai.base import ImageResult
from app.ai.prompts import build_analysis_prompt
from app.config import Settings
from app.errors import (
    AIResponseError,
    AppError,
    ContentBlockedError,
    RateLimitedError,
    ServiceUnavailableError,
    UpstreamError,
    UpstreamRejectedError,
    UpstreamTimeoutError,
)
from app.schemas import AnalysisPayload, GameConceptRequest

logger = logging.getLogger("gamecraft.gemini")
T = TypeVar("T")
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class GeminiProvider:
    name = "gemini"

    def __init__(self, settings: Settings):
        from google import genai
        from google.genai import errors as genai_errors
        from google.genai import types

        if not settings.gemini_api_key:
            raise ServiceUnavailableError("GEMINI_API_KEY is not configured")
        self._s = settings
        self._types = types
        self._api_error = genai_errors.APIError
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=int(settings.ai_timeout_seconds * 1000)),
        )

    # ------------------------------------------------------------------ helpers
    async def _run(self, fn: Callable[[], T]) -> T:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(fn), timeout=self._s.ai_timeout_seconds + 5
            )
        except AppError:
            raise
        except TimeoutError as exc:
            raise UpstreamTimeoutError() from exc
        except Exception as exc:  # noqa: BLE001 - classify everything the SDK can throw
            raise self._classify(exc) from exc

    def _classify(self, exc: Exception) -> AppError:
        logger.warning("Gemini call failed: %s: %s", type(exc).__name__, exc)
        if isinstance(exc, self._api_error):
            code = getattr(exc, "code", None)
            if code == 429:
                return RateLimitedError("The AI provider is rate limiting us. Retrying shortly.")
            if code in (401, 403):
                return ServiceUnavailableError("AI provider credentials were rejected.")
            if code == 400:
                return UpstreamRejectedError()
            return UpstreamError()
        if "timeout" in type(exc).__name__.lower():
            return UpstreamTimeoutError()
        return UpstreamError()

    def _check_blocked(self, response: Any) -> None:
        feedback = getattr(response, "prompt_feedback", None)
        if feedback is not None and getattr(feedback, "block_reason", None):
            raise ContentBlockedError()
        for cand in getattr(response, "candidates", None) or []:
            reason = str(getattr(cand, "finish_reason", "") or "").upper()
            if any(tag in reason for tag in ("SAFETY", "PROHIBITED", "BLOCKLIST", "IMAGE_SAFETY")):
                raise ContentBlockedError()

    # ------------------------------------------------------------------ analyze
    async def analyze(self, concept: GameConceptRequest) -> tuple[AnalysisPayload, str]:
        prompt = build_analysis_prompt(concept)
        models = [self._s.thinking_model]
        if self._s.fallback_model and self._s.fallback_model != self._s.thinking_model:
            models.append(self._s.fallback_model)

        for idx, model in enumerate(models):
            try:
                response = await self._run(lambda m=model, first=(idx == 0): self._generate_json(m, prompt, first))
            except AppError as exc:
                # Model unavailable on this account -> try the fallback model once.
                if isinstance(exc, UpstreamError) and idx < len(models) - 1 and getattr(exc.__cause__, "code", None) == 404:
                    logger.warning("Model %s not found, falling back to %s", model, models[idx + 1])
                    continue
                raise
            self._check_blocked(response)
            return self._parse_analysis(response), model
        raise UpstreamError()  # pragma: no cover

    def _generate_json(self, model: str, prompt: str, use_thinking: bool) -> Any:
        types = self._types
        kwargs: dict[str, Any] = {"response_mime_type": "application/json"}
        level = getattr(types, "ThinkingLevel", None)
        if use_thinking and level is not None and hasattr(level, "HIGH"):
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=level.HIGH)
        return self._client.models.generate_content(
            model=model, contents=prompt, config=types.GenerateContentConfig(**kwargs)
        )

    @staticmethod
    def _parse_analysis(response: Any) -> AnalysisPayload:
        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise AIResponseError("The AI provider returned an empty analysis.")
        try:
            return AnalysisPayload.model_validate(json.loads(_FENCE_RE.sub("", text)))
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Unusable analysis payload: %s", exc)
            raise AIResponseError("The AI provider returned an analysis that did not match the expected format.") from exc

    # ------------------------------------------------------------------- images
    async def generate_image(self, *, prompt: str, aspect_ratio: str, seed: int | None = None) -> ImageResult:
        response = await self._run(lambda: self._generate_image_sync(prompt, aspect_ratio, seed))
        self._check_blocked(response)
        for cand in getattr(response, "candidates", None) or []:
            content = getattr(cand, "content", None)
            for part in (getattr(content, "parts", None) or []):
                inline = getattr(part, "inline_data", None)
                if inline is not None and inline.data:
                    data = inline.data
                    if isinstance(data, str):  # some SDK paths hand back base64 text
                        import base64

                        data = base64.b64decode(data)
                    return ImageResult(data=bytes(data), mime_type=inline.mime_type or "image/png")
        raise AIResponseError("The AI provider returned no image for this prompt.")

    def _generate_image_sync(self, prompt: str, aspect_ratio: str, seed: int | None) -> Any:
        types = self._types
        cfg: dict[str, Any] = {
            "response_modalities": ["IMAGE"],
            "image_config": types.ImageConfig(aspect_ratio=aspect_ratio),
        }
        if seed is not None:
            cfg["seed"] = seed
        return self._client.models.generate_content(
            model=self._s.image_model,
            contents=prompt,
            config=types.GenerateContentConfig(**cfg),
        )
