"""Pydantic v2 request/response contracts."""

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_HEX_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------
class ArtStyleEnum(str, Enum):
    PIXEL_ART = "pixel_art"
    LOW_POLY_3D = "low_poly_3d"
    HAND_PAINTED_FANTASY = "hand_painted_fantasy"
    SCI_FI_VECTOR = "sci_fi_vector"
    RETRO_ANIME = "retro_anime"
    DARK_GOTHIC = "dark_gothic"
    CUSTOM = "custom"


class AssetCategoryEnum(str, Enum):
    CHARACTER = "character"
    ENVIRONMENT = "environment"
    WEAPON = "weapon"
    ICON = "icon"


class AspectRatioEnum(str, Enum):
    SQUARE = "1:1"
    STANDARD = "4:3"
    WIDESCREEN = "16:9"


class AssetStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # some assets succeeded, some failed
    FAILED = "failed"


class EngineTarget(str, Enum):
    UNIVERSAL = "universal"
    GODOT = "godot"
    UNITY = "unity"
    UNREAL = "unreal"


# --------------------------------------------------------------------------
# Art bible + blueprints
# --------------------------------------------------------------------------
class ColorPaletteItem(BaseModel):
    hex: str = Field(..., description="Hex color including '#', e.g. '#6366F1'")
    name: str = Field(..., min_length=1, max_length=40, description="Token name, e.g. 'Mana Sapphire'")
    role: str = Field(..., min_length=1, max_length=30, description="'primary', 'accent', 'shadow', 'highlight'...")

    @field_validator("hex")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        if not _HEX_RE.match(v):
            raise ValueError("hex must look like '#RGB' or '#RRGGBB'")
        return v.upper()


class AssetBlueprint(BaseModel):
    category: AssetCategoryEnum
    name: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., max_length=500, description="In-game lore or mechanical description")
    prompt: str = Field(..., min_length=5, max_length=1500, description="Image generation prompt")
    negative_prompt: str | None = Field(None, max_length=500)
    suggested_aspect_ratio: AspectRatioEnum = AspectRatioEnum.SQUARE


class ArtBible(BaseModel):
    theme_summary: str = Field(..., max_length=600)
    palette: list[ColorPaletteItem] = Field(..., min_length=3, max_length=8)
    lighting_atmosphere: str = Field(..., max_length=600)
    silhouette_guidelines: str = Field(..., max_length=600)
    style_keywords: list[str] = Field(..., min_length=1, max_length=12)


class AnalysisPayload(BaseModel):
    """What the 'thinking' model must return. Validated before anything is stored."""

    art_bible: ArtBible
    blueprints: list[AssetBlueprint] = Field(..., min_length=4, max_length=8)

    @model_validator(mode="after")
    def all_categories_present(self) -> "AnalysisPayload":
        missing = {c for c in AssetCategoryEnum} - {b.category for b in self.blueprints}
        if missing:
            names = ", ".join(sorted(m.value for m in missing))
            raise ValueError(f"blueprints missing categories: {names}")
        return self


# --------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------
class GameConceptRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "Chrono Depths",
                "genre": "Metroidvania Roguelike",
                "synopsis": "An agile diver fights clockwork leviathans in a submerged steampunk abyss to reignite the Sun Engine.",
                "art_style": "pixel_art",
                "custom_art_notes": "Bioluminescent cyan caustics, brass machinery, dark obsidian stone.",
            }
        },
    )

    title: str = Field(..., min_length=2, max_length=120)
    genre: str = Field(..., min_length=2, max_length=80)
    synopsis: str = Field(..., min_length=10, max_length=2000)
    art_style: ArtStyleEnum = ArtStyleEnum.PIXEL_ART
    custom_art_notes: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def custom_style_needs_notes(self) -> "GameConceptRequest":
        if self.art_style == ArtStyleEnum.CUSTOM and not self.custom_art_notes:
            raise ValueError("custom_art_notes is required when art_style is 'custom'")
        return self


class AssetGenerateRequest(BaseModel):
    """Generate one asset. The art style always comes from the project."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "project_id": "3f2b8c1e-0000-0000-0000-000000000000",
                "category": "character",
                "name": "Chrono Diver Scout",
                "prompt": "deep-sea diver in combat stance with glowing harpoon, full body, dark backdrop",
                "aspect_ratio": "1:1",
            }
        },
    )

    project_id: str = Field(..., min_length=1, max_length=64)
    category: AssetCategoryEnum
    name: str = Field(..., min_length=1, max_length=80)
    prompt: str = Field(..., min_length=5, max_length=1500)
    aspect_ratio: AspectRatioEnum = AspectRatioEnum.SQUARE
    negative_prompt: str | None = Field(None, max_length=500)
    seed: int | None = Field(None, ge=0, le=2**31 - 1)


class BatchGenerateRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64)
    # Omit to generate the blueprints produced by /analyze for this project.
    blueprints: list[AssetBlueprint] | None = Field(None, min_length=1, max_length=8)


class RegenerateRequest(BaseModel):
    seed: int | None = Field(None, ge=0, le=2**31 - 1)


# --------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------
class ErrorInfo(BaseModel):
    code: str
    message: str


class AssetOut(BaseModel):
    id: str
    project_id: str
    job_id: str | None = None
    category: AssetCategoryEnum
    name: str
    description: str | None = None
    prompt: str
    aspect_ratio: AspectRatioEnum
    art_style: ArtStyleEnum
    status: AssetStatus
    image_url: str | None = Field(None, description="Relative URL of the image; set once status is 'completed'")
    error: ErrorInfo | None = None
    created_at: datetime


class ProjectOut(BaseModel):
    project_id: str
    title: str
    genre: str
    synopsis: str
    art_style: ArtStyleEnum
    custom_art_notes: str | None = None
    art_bible: ArtBible
    blueprints: list[AssetBlueprint]
    model_used: str
    created_at: datetime


class ProjectDetail(ProjectOut):
    assets: list[AssetOut]


class JobOut(BaseModel):
    job_id: str
    project_id: str
    status: JobStatus
    total: int
    completed: int
    failed: int
    assets: list[AssetOut]
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
    provider: str
    thinking_model: str
    image_model: str
    database: str


class StyleInfo(BaseModel):
    id: ArtStyleEnum
    label: str


class CatalogResponse(BaseModel):
    art_styles: list[StyleInfo]
    categories: list[AssetCategoryEnum]
    aspect_ratios: list[AspectRatioEnum]
    engine_targets: list[EngineTarget]
    max_batch_size: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
