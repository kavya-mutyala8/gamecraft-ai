"""Filesystem storage for generated images (swap for S3/GCS behind the same interface)."""

import os
import tempfile
from pathlib import Path

_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def extension_for(mime_type: str) -> str:
    return _EXT.get(mime_type, ".bin")


class Storage:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, project_id: str, asset_id: str, data: bytes, mime_type: str) -> str:
        """Write atomically; returns the path relative to the storage root."""
        rel = f"{project_id}/{asset_id}{extension_for(mime_type)}"
        target = self._resolve(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.replace(tmp, target)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return rel

    def read(self, rel: str) -> bytes:
        return self._resolve(rel).read_bytes()

    def path(self, rel: str) -> Path:
        return self._resolve(rel)

    def _resolve(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError("path escapes storage root")
        return p
