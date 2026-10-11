import time

import pytest
from fastapi.testclient import TestClient

from app.ai.mock import MockProvider
from app.config import Settings
from app.errors import ContentBlockedError, UpstreamError
from app.main import create_app

CONCEPT = {
    "title": "Chrono Depths",
    "genre": "Metroidvania Roguelike",
    "synopsis": "A diver fights clockwork leviathans in a submerged steampunk abyss.",
    "art_style": "pixel_art",
}


def make_settings(tmp_path, **overrides) -> Settings:
    base = dict(
        environment="test",
        ai_provider="mock",
        database_url=f"sqlite:///{tmp_path}/test.db",
        storage_dir=tmp_path / "storage",
        ai_retry_base_delay=0.0,
        ai_max_retries=1,
        rate_limit_per_minute=0,
    )
    base.update(overrides)
    return Settings(**base)


class FlakyProvider(MockProvider):
    """Weapon images are 'blocked'; everything else works."""

    async def generate_image(self, *, prompt, aspect_ratio, seed=None):
        if "Single weapon shown" in prompt:
            raise ContentBlockedError()
        return await super().generate_image(prompt=prompt, aspect_ratio=aspect_ratio, seed=seed)


class DownProvider(MockProvider):
    calls = 0

    async def generate_image(self, *, prompt, aspect_ratio, seed=None):
        type(self).calls += 1
        raise UpstreamError()


@pytest.fixture
def make_client(tmp_path):
    clients = []

    def _make(provider=None, **overrides):
        c = TestClient(create_app(make_settings(tmp_path, **overrides), provider=provider))
        c.__enter__()  # runs lifespan; keeps one event loop alive so background jobs progress
        clients.append(c)
        return c

    yield _make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def project(client):
    r = client.post("/api/v1/analyze", json=CONCEPT)
    assert r.status_code == 201, r.text
    return r.json()


def wait_for_job(client, job_id, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/v1/jobs/{job_id}").json()
        if job["status"] not in ("queued", "running"):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish in time")
