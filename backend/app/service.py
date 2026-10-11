"""Server-side orchestration: analyze -> persist -> generate (single / batch job) -> export."""

import asyncio
import io
import json
import logging
import random
import re
import uuid
import zipfile
from pathlib import Path
from typing import Awaitable, Callable, TypeVar

from sqlalchemy import select, update

from app.ai.base import AIProvider
from app.ai.prompts import build_image_prompt
from app.config import Settings
from app.db import Asset, Database, Job, Project, utcnow
from app.errors import (
    RETRYABLE,
    AppError,
    ConflictError,
    NotFoundError,
    RateLimitedError,
)
from app.mappers import asset_out, job_out, project_detail, project_out
from app.schemas import (
    ArtBible,
    ArtStyleEnum,
    AssetBlueprint,
    AssetCategoryEnum,
    AssetGenerateRequest,
    AssetOut,
    AssetStatus,
    BatchGenerateRequest,
    EngineTarget,
    GameConceptRequest,
    JobOut,
    JobStatus,
    ProjectDetail,
    ProjectOut,
)
from app.storage import Storage, extension_for

logger = logging.getLogger("gamecraft.service")
T = TypeVar("T")

_ENGINE_ROOTS = {
    EngineTarget.UNIVERSAL: "assets",
    EngineTarget.GODOT: "assets/gamecraft",
    EngineTarget.UNITY: "Assets/GameCraft",
    EngineTarget.UNREAL: "Content/GameCraft",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "asset"


class GenerationService:
    def __init__(self, *, provider: AIProvider, db: Database, storage: Storage, settings: Settings):
        self.provider = provider
        self.db = db
        self.storage = storage
        self.settings = settings
        self._sem = asyncio.Semaphore(settings.max_parallel_generations)
        self._tasks: set[asyncio.Task] = set()

    # ------------------------------------------------------------- lifecycle
    def recover_interrupted_work(self) -> None:
        """Jobs run in-process, so anything still active at boot was killed by a restart."""
        with self.db.session() as s:
            s.execute(
                update(Job)
                .where(Job.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]))
                .values(status=JobStatus.FAILED.value, updated_at=utcnow())
            )
            s.execute(
                update(Asset)
                .where(Asset.status.in_([AssetStatus.PENDING.value, AssetStatus.GENERATING.value]))
                .values(
                    status=AssetStatus.FAILED.value,
                    error_code="SERVER_RESTARTED",
                    error_message="Generation was interrupted by a server restart. Regenerate this asset.",
                )
            )

    async def shutdown(self) -> None:
        for t in list(self._tasks):
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    # ---------------------------------------------------------------- retries
    async def _with_retries(self, factory: Callable[[], Awaitable[T]]) -> T:
        attempt = 0
        while True:
            try:
                return await factory()
            except RETRYABLE as exc:
                if attempt >= self.settings.ai_max_retries:
                    raise
                delay = self.settings.ai_retry_base_delay * (2**attempt) + random.uniform(0, 0.25)
                if isinstance(exc, RateLimitedError) and exc.retry_after:
                    delay = max(delay, exc.retry_after)
                logger.info("Retrying after %s (attempt %d, sleeping %.2fs)", exc.code, attempt + 1, delay)
                attempt += 1
                await asyncio.sleep(delay)

    # ---------------------------------------------------------------- projects
    async def analyze(self, concept: GameConceptRequest) -> ProjectOut:
        payload, model_used = await self._with_retries(lambda: self.provider.analyze(concept))
        project = Project(
            id=str(uuid.uuid4()),
            title=concept.title,
            genre=concept.genre,
            synopsis=concept.synopsis,
            art_style=concept.art_style.value,
            custom_art_notes=concept.custom_art_notes,
            art_bible=payload.art_bible.model_dump(mode="json"),
            blueprints=[b.model_dump(mode="json") for b in payload.blueprints],
            model_used=model_used,
        )
        with self.db.session() as s:
            s.add(project)
        return project_out(project)

    def _get_project(self, project_id: str) -> Project:
        with self.db.session() as s:
            project = s.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' was not found.")
        return project

    def get_project_detail(self, project_id: str) -> ProjectDetail:
        with self.db.session() as s:
            project = s.get(Project, project_id)
            if project is None:
                raise NotFoundError(f"Project '{project_id}' was not found.")
            assets = list(s.scalars(select(Asset).where(Asset.project_id == project_id).order_by(Asset.created_at)))
            return project_detail(project, assets)

    # ----------------------------------------------------------- single asset
    async def generate_single(self, req: AssetGenerateRequest) -> AssetOut:
        project = self._get_project(req.project_id)
        asset = Asset(
            id=str(uuid.uuid4()),
            project_id=project.id,
            category=req.category.value,
            name=req.name,
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            aspect_ratio=req.aspect_ratio.value,
            art_style=project.art_style,
            seed=req.seed,
            status=AssetStatus.PENDING.value,
        )
        with self.db.session() as s:
            s.add(asset)
        await self._render(asset.id)  # raises a typed AppError on failure
        return self._asset(asset.id)

    async def regenerate(self, asset_id: str, seed: int | None) -> AssetOut:
        with self.db.session() as s:
            asset = s.get(Asset, asset_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' was not found.")
            if asset.status in (AssetStatus.PENDING.value, AssetStatus.GENERATING.value):
                raise ConflictError("This asset is still being generated.")
            asset.status = AssetStatus.PENDING.value
            asset.error_code = asset.error_message = asset.file_path = asset.mime_type = None
            if seed is not None:
                asset.seed = seed
        await self._render(asset_id)
        return self._asset(asset_id)

    def _asset(self, asset_id: str) -> AssetOut:
        with self.db.session() as s:
            asset = s.get(Asset, asset_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' was not found.")
            return asset_out(asset)

    def get_asset(self, asset_id: str) -> AssetOut:
        return self._asset(asset_id)

    def get_asset_file(self, asset_id: str) -> tuple[Path, str]:
        with self.db.session() as s:
            asset = s.get(Asset, asset_id)
        if asset is None:
            raise NotFoundError(f"Asset '{asset_id}' was not found.")
        if asset.status != AssetStatus.COMPLETED.value or not asset.file_path:
            raise ConflictError(f"Asset image is not ready (status: {asset.status}).")
        return self.storage.path(asset.file_path), asset.mime_type or "application/octet-stream"

    # -------------------------------------------------------------- rendering
    def _set_asset(self, asset_id: str, **values) -> None:
        with self.db.session() as s:
            s.execute(update(Asset).where(Asset.id == asset_id).values(**values))

    async def _render(self, asset_id: str) -> None:
        with self.db.session() as s:
            asset = s.get(Asset, asset_id)
            project = s.get(Project, asset.project_id)
        art_bible = ArtBible.model_validate(project.art_bible)
        full_prompt = build_image_prompt(
            prompt=asset.prompt,
            category=AssetCategoryEnum(asset.category),
            art_style=ArtStyleEnum(project.art_style),
            custom_notes=project.custom_art_notes,
            art_bible=art_bible,
            negative_prompt=asset.negative_prompt,
        )
        try:
            async with self._sem:
                self._set_asset(asset_id, status=AssetStatus.GENERATING.value)
                image = await self._with_retries(
                    lambda: self.provider.generate_image(
                        prompt=full_prompt, aspect_ratio=asset.aspect_ratio, seed=asset.seed
                    )
                )
            rel = await asyncio.to_thread(
                self.storage.save, asset.project_id, asset_id, image.data, image.mime_type
            )
            self._set_asset(
                asset_id,
                status=AssetStatus.COMPLETED.value,
                file_path=rel,
                mime_type=image.mime_type,
                error_code=None,
                error_message=None,
            )
        except asyncio.CancelledError:
            self._set_asset(asset_id, status=AssetStatus.FAILED.value, error_code="CANCELLED", error_message="Generation was cancelled.")
            raise
        except AppError as exc:
            self._set_asset(asset_id, status=AssetStatus.FAILED.value, error_code=exc.code, error_message=exc.message)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected failure rendering asset %s", asset_id)
            self._set_asset(asset_id, status=AssetStatus.FAILED.value, error_code="INTERNAL_ERROR", error_message="Unexpected error while generating this asset.")
            raise AppError() from exc

    # ------------------------------------------------------------ batch jobs
    async def start_batch(self, req: BatchGenerateRequest) -> JobOut:
        project = self._get_project(req.project_id)
        blueprints = req.blueprints or [AssetBlueprint.model_validate(b) for b in project.blueprints]
        if len(blueprints) > self.settings.max_batch_size:
            raise ConflictError(f"A batch can contain at most {self.settings.max_batch_size} assets.")

        job_id = str(uuid.uuid4())
        with self.db.session() as s:
            active = s.scalars(
                select(Job.id).where(
                    Job.project_id == project.id,
                    Job.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]),
                )
            ).first()
            if active:
                raise ConflictError("A generation job is already running for this project.", details={"job_id": active})
            job = Job(id=job_id, project_id=project.id, total=len(blueprints), status=JobStatus.QUEUED.value)
            s.add(job)
            s.flush()  # job row must exist before assets reference it
            assets = [
                Asset(
                    id=str(uuid.uuid4()),
                    project_id=project.id,
                    job_id=job_id,
                    category=bp.category.value,
                    name=bp.name,
                    description=bp.description,
                    prompt=bp.prompt,
                    negative_prompt=bp.negative_prompt,
                    aspect_ratio=bp.suggested_aspect_ratio.value,
                    art_style=project.art_style,
                    status=AssetStatus.PENDING.value,
                )
                for bp in blueprints
            ]
            s.add_all(assets)
            s.flush()
            snapshot = job_out(job, assets)

        task = asyncio.create_task(self._run_job(job_id), name=f"job-{job_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return snapshot

    def _set_job(self, job_id: str, **values) -> None:
        with self.db.session() as s:
            s.execute(update(Job).where(Job.id == job_id).values(updated_at=utcnow(), **values))

    def _bump_job(self, job_id: str, ok: bool) -> None:
        # No await between read and write, so this is atomic on the event loop.
        with self.db.session() as s:
            job = s.get(Job, job_id)
            if ok:
                job.completed += 1
            else:
                job.failed += 1
            job.updated_at = utcnow()

    async def _run_job(self, job_id: str) -> None:
        try:
            self._set_job(job_id, status=JobStatus.RUNNING.value)
            with self.db.session() as s:
                asset_ids = list(s.scalars(select(Asset.id).where(Asset.job_id == job_id).order_by(Asset.created_at)))

            async def one(asset_id: str) -> None:
                try:
                    await self._render(asset_id)
                    self._bump_job(job_id, True)
                except asyncio.CancelledError:
                    raise
                except Exception:  # noqa: BLE001 - already recorded on the asset
                    self._bump_job(job_id, False)

            await asyncio.gather(*(one(a) for a in asset_ids))

            with self.db.session() as s:
                job = s.get(Job, job_id)
                if job.failed == 0:
                    final = JobStatus.COMPLETED
                elif job.completed == 0:
                    final = JobStatus.FAILED
                else:
                    final = JobStatus.PARTIAL
            self._set_job(job_id, status=final.value)
        except asyncio.CancelledError:
            self._set_job(job_id, status=JobStatus.FAILED.value)
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Job %s crashed", job_id)
            self._set_job(job_id, status=JobStatus.FAILED.value)

    def get_job(self, job_id: str) -> JobOut:
        with self.db.session() as s:
            job = s.get(Job, job_id)
            if job is None:
                raise NotFoundError(f"Job '{job_id}' was not found.")
            assets = list(s.scalars(select(Asset).where(Asset.job_id == job_id).order_by(Asset.created_at)))
            return job_out(job, assets)

    # ----------------------------------------------------------------- export
    def build_export_zip(self, project_id: str, engine: EngineTarget) -> tuple[bytes, str]:
        with self.db.session() as s:
            project = s.get(Project, project_id)
            if project is None:
                raise NotFoundError(f"Project '{project_id}' was not found.")
            assets = list(
                s.scalars(
                    select(Asset)
                    .where(Asset.project_id == project_id, Asset.status == AssetStatus.COMPLETED.value)
                    .order_by(Asset.created_at)
                )
            )
        if not assets:
            raise ConflictError("This project has no completed assets to export yet.")

        root = _ENGINE_ROOTS[engine]
        manifest_assets, used = [], set()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for a in assets:
                base = f"{root}/{a.category}/{_slug(a.name)}"
                path, n = f"{base}{extension_for(a.mime_type or '')}", 2
                while path in used:
                    path, n = f"{base}_{n}{extension_for(a.mime_type or '')}", n + 1
                used.add(path)
                zf.writestr(path, self.storage.read(a.file_path))
                manifest_assets.append(
                    {"id": a.id, "name": a.name, "category": a.category, "file": path,
                     "aspect_ratio": a.aspect_ratio, "prompt": a.prompt, "seed": a.seed}
                )
            manifest = {
                "project": {"id": project.id, "title": project.title, "genre": project.genre, "art_style": project.art_style},
                "engine_target": engine.value,
                "art_bible": project.art_bible,
                "assets": manifest_assets,
            }
            zf.writestr(f"{root}/manifest.json", json.dumps(manifest, indent=2))
        return buf.getvalue(), f"{_slug(project.title)}_{engine.value}.zip"
