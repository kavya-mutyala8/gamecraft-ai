import pytest
from pydantic import ValidationError

from app.schemas import (
    AnalysisPayload,
    ArtStyleEnum,
    AssetBlueprint,
    AssetCategoryEnum,
    ColorPaletteItem,
    GameConceptRequest,
)


def test_valid_concept():
    req = GameConceptRequest(
        title="Abyssal Chronomancer", genre="Metroidvania", synopsis="A chrono-diver navigates clockwork catacombs."
    )
    assert req.art_style == ArtStyleEnum.PIXEL_ART


def test_short_synopsis_rejected():
    with pytest.raises(ValidationError):
        GameConceptRequest(title="Short", genre="RPG", synopsis="Too short")


def test_custom_style_requires_notes():
    with pytest.raises(ValidationError):
        GameConceptRequest(title="Custom", genre="RPG", synopsis="A long enough synopsis here.", art_style="custom")


def test_hex_validation_and_normalization():
    assert ColorPaletteItem(hex="#6366f1", name="Indigo", role="primary").hex == "#6366F1"
    with pytest.raises(ValidationError):
        ColorPaletteItem(hex="blue", name="Blue", role="primary")
    with pytest.raises(ValidationError):
        ColorPaletteItem(hex="#12345", name="Bad", role="primary")


def test_blueprint_defaults():
    bp = AssetBlueprint(category="weapon", name="Glaive", description="Polearm", prompt="16-bit pixel art weapon")
    assert bp.suggested_aspect_ratio.value == "1:1"


def test_analysis_payload_requires_all_categories():
    from app.ai.mock import MockProvider
    import asyncio

    payload, _ = asyncio.run(
        MockProvider().analyze(GameConceptRequest(title="Test Game", genre="RPG", synopsis="A long enough synopsis."))
    )
    data = payload.model_dump(mode="json")
    data["blueprints"] = [b for b in data["blueprints"] if b["category"] != AssetCategoryEnum.ICON.value] * 2
    with pytest.raises(ValidationError):
        AnalysisPayload.model_validate(data)
