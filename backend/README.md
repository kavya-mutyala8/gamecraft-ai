# GameCraft AI - Backend (FastAPI)

Concept + art style in -> Art Bible + matching asset pack (characters, environments, weapons, icons) out.

## Run

```bash
pip install -r requirements-dev.txt
cp .env.example .env            # add GEMINI_API_KEY for real generation
uvicorn app.main:app --reload   # docs at http://localhost:8000/docs
pytest
```

With no `GEMINI_API_KEY` the server uses an offline mock provider (gradient SVG placeholders), so the
frontend can be built end to end first. With a key set, Gemini is used and failures are **reported, never faked**.

## Layout

```
app/
  main.py        app factory, CORS, request-id, error envelope
  config.py      env settings (models, limits, CORS, DB)
  schemas.py     Pydantic contracts + enums
  errors.py      typed errors -> HTTP status + stable error codes
  service.py     orchestration: analyze, single, batch jobs, retries, export
  ai/            provider interface, prompts, Gemini provider, offline mock
  api/v1.py      routes
  db.py          SQLAlchemy models (projects, jobs, assets)
  storage.py     image files on disk (swap for S3/GCS)
  ratelimit.py   per-IP limiter for generation routes
tests/
```

## Flow

1. `POST /api/v1/analyze` -> creates a **project**: Art Bible (palette, lighting, shape language) + 4 blueprints.
2. `POST /api/v1/generate/batch {project_id}` -> `202` + job. Poll `GET /api/v1/jobs/{job_id}`.
3. Show each asset's `image_url` (`GET /api/v1/assets/{id}/image`). Tweak with `POST /assets/{id}/regenerate`.
4. `GET /api/v1/projects/{id}/export?engine=unity|godot|unreal|universal` -> ZIP + `manifest.json`.

Every image prompt is wrapped with the project's locked style, palette and lighting, which is what keeps the set cohesive.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/health` | 503 if DB unreachable |
| GET | `/api/v1/catalog` | styles, categories, ratios for UI pickers |
| POST | `/api/v1/analyze` | 201, rate limited |
| GET | `/api/v1/projects/{id}` | project + all assets |
| POST | `/api/v1/generate/single` | 201, synchronous |
| POST | `/api/v1/generate/batch` | 202, async job; `blueprints` optional |
| GET | `/api/v1/jobs/{id}` | `queued/running/completed/partial/failed` + per-asset status |
| GET | `/api/v1/assets/{id}` , `/image` | metadata / binary image |
| POST | `/api/v1/assets/{id}/regenerate` | optional `{seed}` |
| GET | `/api/v1/projects/{id}/export` | ZIP download |

## Errors

All errors share one shape; switch on `error.code`, not the message:

```json
{"error": {"code": "CONTENT_BLOCKED", "message": "...", "details": null, "request_id": "..."}}
```

| Code | HTTP | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | bad payload; `details[]` lists `field` + `message` |
| `NOT_FOUND` | 404 | unknown project/job/asset/route |
| `CONFLICT` | 409 | job already running, image not ready, nothing to export |
| `CONTENT_BLOCKED` | 422 | provider safety filter refused the prompt/output |
| `RATE_LIMITED` | 429 | see `Retry-After` header |
| `UPSTREAM_ERROR` / `AI_BAD_RESPONSE` | 502 | provider failed or returned something unusable (auto-retried first) |
| `UPSTREAM_TIMEOUT` | 504 | provider too slow |
| `SERVICE_UNAVAILABLE` | 503 | e.g. provider credentials rejected |

In a batch, one failed asset never fails the pack: the job ends `partial` and the failed asset carries its own `error`.

## Frontend snippet

```js
const api = "http://localhost:8000/api/v1";
const post = (p, b) => fetch(api + p, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b)}).then(async r => { if (!r.ok) throw (await r.json()).error; return r.json(); });

const project = await post("/analyze", {title, genre, synopsis, art_style: "pixel_art"});
let job = await post("/generate/batch", {project_id: project.project_id});
while (["queued", "running"].includes(job.status)) {
  await new Promise(r => setTimeout(r, 1500));
  job = await fetch(`${api}/jobs/${job.job_id}`).then(r => r.json());   // render job.assets as they complete
}
```

## Changes from the draft in backend.zip

- One package instead of duplicated root/`fastapi/`/`flask/` copies (the folder named `fastapi/` also shadowed the real library).
- `/analyze` previously called Gemini then **discarded the answer** and returned hardcoded data; it now validates the model's JSON and stores it.
- Image failures were swallowed and returned `status: "completed"` with an empty URL; they now raise typed errors (and the asset is stored as `failed`).
- Image bytes were base64-encoded incorrectly (`b'...'` repr); images are now saved as files and served from `/assets/{id}/image`.
- Errors no longer leak `str(exception)`; validation errors are JSON-safe; CORS is an allow-list instead of `*`.
- Batch generation is an async job with bounded parallelism, retry/backoff, and partial-failure reporting.
- `art_style` is taken from the project, not trusted per request. `/export/bundle` (a stub) became `GET /projects/{id}/export`.
- Dropped the Flask copy: it had no validation and only stub image generation.

## Production notes

- Jobs run in-process (`asyncio`); a restart marks in-flight work `failed` (users can regenerate). For multiple
  instances, move to a queue (Celery/RQ/arq) and Redis-backed rate limiting. Run a single worker until then.
- Add authentication/per-user ownership before exposing publicly; project IDs are unguessable UUIDs but not secret.
- Model IDs in `.env.example` come from your draft and are unverified; confirm them against your Gemini account.

# How to run the Gamecraft backend

1. **Navigate to the backend directory:**
   ```powershell
   cd "C:\Users\ADMIN\OneDrive\Desktop\gamecraft-backend"
   ```

2. **Install the required dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Start the development server:**
   ```powershell
   python -m uvicorn app.main:app --reload
   ```

The server will be live and accessible at `http://127.0.0.1:8000`.
