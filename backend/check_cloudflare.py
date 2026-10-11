"""Quick test of your Cloudflare keys, before starting the whole app.

Run from the backend folder (venv active):   python check_cloudflare.py
It makes ONE image and saves it as cloudflare_test.jpg (or .png).
"""
import asyncio

from app.ai.cloudflare import CloudflareProvider
from app.config import get_settings


async def main() -> None:
    provider = CloudflareProvider(get_settings())
    img = await provider.generate_image(prompt="pixel art potion bottle, game inventory icon, centered, plain background", aspect_ratio="1:1")
    ext = {"image/png": "png", "image/webp": "webp"}.get(img.mime_type, "jpg")
    path = f"cloudflare_test.{ext}"
    open(path, "wb").write(img.data)
    print(f"OK: saved {path} ({len(img.data)} bytes, {img.mime_type})")


asyncio.run(main())
