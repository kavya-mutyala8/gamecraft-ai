"""Cloudflare Workers AI provider (free tier).

Images: FLUX.1 schnell.  Art bible + blueprints: a Llama text model. If the text model fails
or returns something unusable, we fall back to the built-in art bible (enriched with the user's
concept) so generation still works. Bad credentials are NOT hidden: they raise a clear error.
"""

import base64
import json
import logging
import re

import httpx

from app.ai.base import ImageResult
from app.ai.mock import MockProvider
from app.ai.prompts import build_analysis_prompt
from app.config import Settings
from app.errors import (
    AIResponseError,
    RateLimitedError,
    ServiceUnavailableError,
    UpstreamError,
    UpstreamRejectedError,
    UpstreamTimeoutError,
)
from app.schemas import AnalysisPayload, GameConceptRequest

logger = logging.getLogger("gamecraft.cloudflare")

_API = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _sniff_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


class CloudflareProvider:
    name = "cloudflare"

    def __init__(self, settings: Settings):
        if not (settings.cf_account_id and settings.cf_api_token):
            raise ServiceUnavailableError("CF_ACCOUNT_ID and CF_API_TOKEN are not configured")
        self._s = settings
        self._headers = {"Authorization": f"Bearer {settings.cf_api_token}"}
        self._fallback = MockProvider()

    # ------------------------------------------------------------------ http
    async def _run_model(self, model: str, payload: dict) -> httpx.Response:
        url = _API.format(account=self._s.cf_account_id, model=model)
        try:
            async with httpx.AsyncClient(timeout=self._s.ai_timeout_seconds) as client:
                resp = await client.post(url, headers=self._headers, json=payload)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError() from exc
        except httpx.HTTPError as exc:
            logger.warning("Cloudflare request failed: %s: %s", type(exc).__name__, exc)
            raise UpstreamError() from exc
        if resp.status_code >= 400:
            logger.warning("Cloudflare %s -> HTTP %s: %s", model, resp.status_code, resp.text[:300])
            raise self._classify(resp.status_code)
        return resp

    @staticmethod
    def _classify(status: int):
        if status == 429:
            return RateLimitedError("The AI provider is rate limiting us. Retrying shortly.")
        if status in (401, 403):
            return ServiceUnavailableError("AI provider credentials were rejected. Check CF_ACCOUNT_ID and CF_API_TOKEN.")
        if status in (400, 404, 422):
            return UpstreamRejectedError()
        return UpstreamError()

    # ---------------------------------------------------------------- images
    async def generate_image(self, *, prompt: str, aspect_ratio: str, seed: int | None = None) -> ImageResult:
        # FLUX.1 schnell on Workers AI takes a prompt (max ~2048 chars) and steps; no size or seed options.
        resp = await self._run_model(self._s.cf_image_model, {"prompt": prompt[:2000], "steps": 4})
        ctype = resp.headers.get("content-type", "").split(";")[0].strip()
        if ctype.startswith("image/"):
            return ImageResult(data=resp.content, mime_type=ctype)
        try:
            data = base64.b64decode(resp.json()["result"]["image"])
        except (ValueError, KeyError, TypeError) as exc:
            raise AIResponseError("The AI provider returned no image for this prompt.") from exc
        if not data:
            raise AIResponseError("The AI provider returned an empty image.")
        return ImageResult(data=data, mime_type=_sniff_mime(data))

    # --------------------------------------------------------------- analyze
    async def analyze(self, concept: GameConceptRequest) -> tuple[AnalysisPayload, str]:
        try:
            return await self._llm_analysis(concept), self._s.cf_text_model
        except ServiceUnavailableError:
            raise  # wrong credentials: tell the user instead of hiding it
        except Exception as exc:  # noqa: BLE001 - anything else: use the built-in art bible
            logger.warning("Cloudflare text model failed (%s: %s); using the built-in art bible", type(exc).__name__, exc)
        payload, _ = await self._fallback.analyze(concept)
        return self._with_concept(payload, concept), "builtin"

    async def _llm_analysis(self, concept: GameConceptRequest) -> AnalysisPayload:
        body = {
            "messages": [
                {"role": "system", "content": "You are a game art director. Reply with ONLY one valid JSON object. No markdown, no commentary."},
                {"role": "user", "content": build_analysis_prompt(concept)},
            ],
            "max_tokens": 2500,  # Workers AI defaults to a small limit that would cut the JSON off
            "temperature": 0.4,
        }
        resp = await self._run_model(self._s.cf_text_model, body)
        result = (resp.json() or {}).get("result") or {}
        raw = result.get("response")
        if isinstance(raw, dict):
            obj = raw
        else:
            text = _FENCE_RE.sub("", (raw or "").strip())
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise AIResponseError("The text model did not return JSON.")
            obj = json.loads(text[start : end + 1])
        return AnalysisPayload.model_validate(obj)

    @staticmethod
    def _with_concept(payload: AnalysisPayload, concept: GameConceptRequest) -> AnalysisPayload:
        """The built-in art bible only knows the title; add the user's concept so images match it."""
        snippet = concept.synopsis[:500]
        blueprints = [
            b.model_copy(update={"prompt": f"{b.prompt}. Game concept: {snippet}"[:1500]}) for b in payload.blueprints
        ]
        return payload.model_copy(update={"blueprints": blueprints})
