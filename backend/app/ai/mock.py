"""Offline provider: deterministic art bible + SVG placeholder images.

Lets the whole API (and the frontend) run with no API key or network.
Never used silently when a real provider is configured.
"""

import hashlib
from xml.sax.saxutils import escape

from app.ai.base import ImageResult
from app.ai.prompts import STYLE_LABELS
from app.schemas import (
    AnalysisPayload,
    ArtBible,
    ArtStyleEnum,
    AspectRatioEnum,
    AssetBlueprint,
    AssetCategoryEnum,
    ColorPaletteItem,
    GameConceptRequest,
)

_PALETTES: dict[ArtStyleEnum, list[tuple[str, str, str]]] = {
    ArtStyleEnum.PIXEL_ART: [("#0EA5E9", "Aether Blue", "primary"), ("#10B981", "Biolume Green", "accent"), ("#F59E0B", "Core Amber", "highlight"), ("#1E1B4B", "Void Obsidian", "shadow")],
    ArtStyleEnum.LOW_POLY_3D: [("#38BDF8", "Facet Sky", "primary"), ("#A3E635", "Moss Shard", "accent"), ("#FB923C", "Ember Tri", "highlight"), ("#1F2937", "Slate Plane", "shadow")],
    ArtStyleEnum.HAND_PAINTED_FANTASY: [("#7C3AED", "Arcane Violet", "primary"), ("#F59E0B", "Gilded Ochre", "accent"), ("#FDE68A", "Candle Glow", "highlight"), ("#2E1065", "Twilight Ink", "shadow")],
    ArtStyleEnum.SCI_FI_VECTOR: [("#22D3EE", "Neon Cyan", "primary"), ("#E879F9", "Plasma Magenta", "accent"), ("#F8FAFC", "Hull White", "highlight"), ("#0F172A", "Deep Space", "shadow")],
    ArtStyleEnum.RETRO_ANIME: [("#F472B6", "Sakura Pop", "primary"), ("#60A5FA", "Cel Sky", "accent"), ("#FEF08A", "Sunburst", "highlight"), ("#312E81", "Night Ink", "shadow")],
    ArtStyleEnum.DARK_GOTHIC: [("#991B1B", "Dried Blood", "primary"), ("#A8A29E", "Bone Ash", "accent"), ("#FDE047", "Candle Flame", "highlight"), ("#0C0A09", "Crypt Black", "shadow")],
    ArtStyleEnum.CUSTOM: [("#6366F1", "Indigo Glow", "primary"), ("#14B8A6", "Teal Signal", "accent"), ("#FACC15", "Gold Spark", "highlight"), ("#111827", "Ink Night", "shadow")],
}

_SIZES = {
    AspectRatioEnum.SQUARE: (512, 512),
    AspectRatioEnum.STANDARD: (640, 480),
    AspectRatioEnum.WIDESCREEN: (768, 432),
}


class MockProvider:
    name = "mock"

    async def analyze(self, concept: GameConceptRequest) -> tuple[AnalysisPayload, str]:
        palette = [ColorPaletteItem(hex=h, name=n, role=r) for h, n, r in _PALETTES[concept.art_style]]
        style = STYLE_LABELS[concept.art_style]
        t = concept.title
        bible = ArtBible(
            theme_summary=f"Unified {style} direction for {t} ({concept.genre}).",
            palette=palette,
            lighting_atmosphere="High-contrast key light with a colored rim light and deep shadows.",
            silhouette_guidelines="Bold, instantly readable silhouettes; rounded hero shapes, angular hazards.",
            style_keywords=[style.lower(), "clean shapes", "game asset", "consistent palette"],
        )
        blueprints = [
            AssetBlueprint(category=AssetCategoryEnum.CHARACTER, name=f"{t} Protagonist", description="The hero in a ready stance.", prompt=f"{style} protagonist for {t}, full body, signature gear, dynamic pose", suggested_aspect_ratio=AspectRatioEnum.SQUARE),
            AssetBlueprint(category=AssetCategoryEnum.ENVIRONMENT, name="Primary Stage Vista", description="The core biome of the game.", prompt=f"{style} environment vista for {t}, layered depth, atmospheric lighting", suggested_aspect_ratio=AspectRatioEnum.WIDESCREEN),
            AssetBlueprint(category=AssetCategoryEnum.WEAPON, name="Signature Weapon", description="The iconic weapon of the setting.", prompt=f"{style} signature weapon for {t}, glowing details, strong silhouette", suggested_aspect_ratio=AspectRatioEnum.SQUARE),
            AssetBlueprint(category=AssetCategoryEnum.ICON, name="Core Resource Icon", description="Main collectible or consumable.", prompt=f"{style} inventory icon for {t}, glowing resource crystal, clean edges", suggested_aspect_ratio=AspectRatioEnum.SQUARE),
        ]
        return AnalysisPayload(art_bible=bible, blueprints=blueprints), "mock"

    async def generate_image(self, *, prompt: str, aspect_ratio: str, seed: int | None = None) -> ImageResult:
        w, h = _SIZES[AspectRatioEnum(aspect_ratio)]
        digest = hashlib.sha256(f"{prompt}|{seed}".encode()).digest()
        c1, c2 = f"#{digest[0]:02X}{digest[1]:02X}{digest[2]:02X}", f"#{digest[3]:02X}{digest[4]:02X}{digest[5]:02X}"
        label = escape(prompt.splitlines()[0][:60])
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/>'
            f'<stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<rect width="100%" height="100%" fill="url(#g)"/>'
            f'<text x="50%" y="50%" fill="#fff" font-family="sans-serif" font-size="16" text-anchor="middle">{label}</text>'
            f'<text x="50%" y="92%" fill="#fff" font-family="sans-serif" font-size="11" text-anchor="middle" opacity="0.7">GameCraft mock image</text>'
            f"</svg>"
        )
        return ImageResult(data=svg.encode("utf-8"), mime_type="image/svg+xml")
