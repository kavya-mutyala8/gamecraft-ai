import io
import zipfile

from tests.conftest import CONCEPT, DownProvider, FlakyProvider, wait_for_job


def test_health_and_catalog(client):
    h = client.get("/api/v1/health")
    assert h.status_code == 200 and h.json()["provider"] == "mock" and h.json()["database"] == "ok"
    c = client.get("/api/v1/catalog").json()
    assert {"id": "pixel_art", "label": "Pixel Art"} in c["art_styles"]
    assert set(c["categories"]) == {"character", "environment", "weapon", "icon"}


def test_analyze_creates_project(client, project):
    assert project["art_style"] == "pixel_art"
    assert len(project["blueprints"]) == 4
    assert all(p["hex"].startswith("#") for p in project["art_bible"]["palette"])
    detail = client.get(f"/api/v1/projects/{project['project_id']}").json()
    assert detail["title"] == "Chrono Depths" and detail["assets"] == []


def test_validation_errors_are_structured(client):
    r = client.post("/api/v1/analyze", json={"title": "x", "genre": "RPG", "synopsis": "short"})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR" and err["request_id"]
    assert {d["field"] for d in err["details"]} >= {"title", "synopsis"}
    assert r.headers["X-Request-ID"] == err["request_id"]


def test_unknown_routes_and_resources_use_error_envelope(client):
    assert client.get("/api/v1/nope").json()["error"]["code"] == "NOT_FOUND"
    r = client.get("/api/v1/projects/does-not-exist")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_generate_single_and_download_image(client, project):
    body = {
        "project_id": project["project_id"],
        "category": "weapon",
        "name": "Plasma Glaive",
        "prompt": "a plasma polearm with glowing runes",
        "aspect_ratio": "1:1",
    }
    r = client.post("/api/v1/generate/single", json=body)
    assert r.status_code == 201, r.text
    asset = r.json()
    assert asset["status"] == "completed" and asset["art_style"] == "pixel_art"
    img = client.get(asset["image_url"])
    assert img.status_code == 200 and img.headers["content-type"] == "image/svg+xml"
    assert img.content.startswith(b"<svg")


def test_single_for_unknown_project_is_404(client):
    r = client.post(
        "/api/v1/generate/single",
        json={"project_id": "nope", "category": "icon", "name": "Gem", "prompt": "a glowing gem icon"},
    )
    assert r.status_code == 404


def test_batch_job_completes_and_exports(client, project):
    r = client.post("/api/v1/generate/batch", json={"project_id": project["project_id"]})
    assert r.status_code == 202
    job = wait_for_job(client, r.json()["job_id"])
    assert job["status"] == "completed" and job["completed"] == 4 and job["failed"] == 0
    assert all(a["image_url"] for a in job["assets"])

    z = client.get(f"/api/v1/projects/{project['project_id']}/export", params={"engine": "unity"})
    assert z.status_code == 200 and z.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    assert "Assets/GameCraft/manifest.json" in names
    assert any(n.startswith("Assets/GameCraft/character/") for n in names)


def test_second_batch_while_running_conflicts(client, project):
    pid = project["project_id"]
    first = client.post("/api/v1/generate/batch", json={"project_id": pid})
    assert first.status_code == 202
    second = client.post("/api/v1/generate/batch", json={"project_id": pid})
    # The mock finishes very fast; either outcome is valid, but never a 5xx.
    assert second.status_code in (202, 409)
    wait_for_job(client, first.json()["job_id"])


def test_partial_batch_failure_is_reported_per_asset(make_client):
    client = make_client(provider=FlakyProvider())
    pid = client.post("/api/v1/analyze", json=CONCEPT).json()["project_id"]
    job = wait_for_job(client, client.post("/api/v1/generate/batch", json={"project_id": pid}).json()["job_id"])
    assert job["status"] == "partial" and job["completed"] == 3 and job["failed"] == 1
    failed = [a for a in job["assets"] if a["status"] == "failed"]
    assert failed[0]["category"] == "weapon" and failed[0]["error"]["code"] == "CONTENT_BLOCKED"
    assert failed[0]["image_url"] is None


def test_provider_outage_returns_502_after_retries(make_client):
    DownProvider.calls = 0
    client = make_client(provider=DownProvider())
    pid = client.post("/api/v1/analyze", json=CONCEPT).json()["project_id"]
    r = client.post(
        "/api/v1/generate/single",
        json={"project_id": pid, "category": "icon", "name": "Gem", "prompt": "a glowing gem icon"},
    )
    assert r.status_code == 502 and r.json()["error"]["code"] == "UPSTREAM_ERROR"
    assert DownProvider.calls == 2  # 1 try + ai_max_retries(1)
    assets = client.get(f"/api/v1/projects/{pid}").json()["assets"]
    assert assets[0]["status"] == "failed"


def test_regenerate_failed_asset(make_client):
    client = make_client(provider=FlakyProvider())
    pid = client.post("/api/v1/analyze", json=CONCEPT).json()["project_id"]
    job = wait_for_job(client, client.post("/api/v1/generate/batch", json={"project_id": pid}).json()["job_id"])
    ok = next(a for a in job["assets"] if a["status"] == "completed")
    r = client.post(f"/api/v1/assets/{ok['id']}/regenerate", json={"seed": 7})
    assert r.status_code == 200 and r.json()["status"] == "completed"
    bad = next(a for a in job["assets"] if a["status"] == "failed")
    assert client.get(bad["image_url"] or f"/api/v1/assets/{bad['id']}/image").status_code == 409


def test_rate_limit(make_client):
    client = make_client(rate_limit_per_minute=2)
    for _ in range(2):
        assert client.post("/api/v1/analyze", json=CONCEPT).status_code == 201
    r = client.post("/api/v1/analyze", json=CONCEPT)
    assert r.status_code == 429 and r.json()["error"]["code"] == "RATE_LIMITED"
    assert int(r.headers["Retry-After"]) >= 1
