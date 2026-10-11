"""Pluggable image backends. Model names are env-configurable because availability/limits change."""
import base64
import io
import os
import time
import urllib.request
from abc import ABC, abstractmethod


class ImageProvider(ABC):
    name = "base"
    supports_reference = False  # can condition on a reference image?

    @abstractmethod
    def generate(self, prompt, reference=None, seed=None) -> bytes:
        """Return PNG/JPEG bytes."""


def with_retry(fn, tries=3, base=2.0):
    for i in range(tries):
        try:
            return fn()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(base * (i + 1))


class MockProvider(ImageProvider):
    name, supports_reference = "mock", True

    def generate(self, prompt, reference=None, seed=None):
        from PIL import Image, ImageDraw
        import hashlib
        h = hashlib.md5(prompt.encode()).digest()
        img = Image.new("RGB", (512, 512), (h[0], h[1], h[2]))
        d = ImageDraw.Draw(img)
        d.text((10, 10), prompt[:60], fill=(255, 255, 255))
        d.text((10, 30), "ref" if reference else "no-ref", fill=(255, 255, 0))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()


class OpenAIProvider(ImageProvider):
    name, supports_reference = "openai", True

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
        self.size = "1024x1024"

    def generate(self, prompt, reference=None, seed=None):
        def call():
            if reference:
                r = self.client.images.edit(model=self.model, image=("ref.png", reference, "image/png"),
                                            prompt=prompt, size=self.size)
            else:
                r = self.client.images.generate(model=self.model, prompt=prompt, size=self.size, quality="low")
            return base64.b64decode(r.data[0].b64_json)
        return with_retry(call)


class GeminiProvider(ImageProvider):
    name, supports_reference = "gemini", True

    def __init__(self):
        from google import genai
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        self.model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

    def generate(self, prompt, reference=None, seed=None):
        def call():
            contents = [prompt]
            if reference:
                from PIL import Image
                contents.append(Image.open(io.BytesIO(reference)))
            r = self.client.models.generate_content(model=self.model, contents=contents)
            for part in r.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    return part.inline_data.data
            raise RuntimeError("Gemini returned no image")
        return with_retry(call)


class ReplicateProvider(ImageProvider):
    name, supports_reference = "replicate", True

    def __init__(self):
        self.t2i = os.getenv("REPLICATE_T2I_MODEL", "black-forest-labs/flux-schnell")
        self.ref = os.getenv("REPLICATE_REF_MODEL", "black-forest-labs/flux-kontext-pro")

    @staticmethod
    def _read(out):
        if isinstance(out, (list, tuple)):
            out = out[0]
        if hasattr(out, "read"):
            return out.read()
        return urllib.request.urlopen(str(out)).read()

    def generate(self, prompt, reference=None, seed=None):
        import replicate

        def call():
            if reference:
                out = replicate.run(self.ref, input={"prompt": prompt, "input_image": io.BytesIO(reference),
                                                     "output_format": "png"})
            else:
                inp = {"prompt": prompt}
                if seed is not None:
                    inp["seed"] = seed
                out = replicate.run(self.t2i, input=inp)
            return self._read(out)
        return with_retry(call)


def get_provider(name=None):
    name = (name or os.getenv("IMAGE_PROVIDER", "mock")).lower()
    return {"mock": MockProvider, "openai": OpenAIProvider, "gemini": GeminiProvider,
            "replicate": ReplicateProvider}[name]()
