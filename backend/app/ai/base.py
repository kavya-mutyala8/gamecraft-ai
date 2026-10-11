"""Provider interface. The service layer only ever talks to this."""

from dataclasses import dataclass
from typing import Protocol

from app.schemas import AnalysisPayload, GameConceptRequest


@dataclass(frozen=True)
class ImageResult:
    data: bytes
    mime_type: str


class AIProvider(Protocol):
    name: str

    async def analyze(self, concept: GameConceptRequest) -> tuple[AnalysisPayload, str]:
        """Return (validated art bible + blueprints, model id actually used)."""
        ...

    async def generate_image(
        self, *, prompt: str, aspect_ratio: str, seed: int | None = None
    ) -> ImageResult:
        """Return one image. Must raise a typed AppError on failure - never return empty data."""
        ...
