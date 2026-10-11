"""ORM rows -> API models."""

from datetime import datetime, timezone

from app.db import Asset, Job, Project
from app.schemas import (
    ArtBible,
    AssetBlueprint,
    AssetOut,
    AssetStatus,
    ErrorInfo,
    JobOut,
    ProjectDetail,
    ProjectOut,
)


def _utc(dt: datetime) -> datetime:
    # SQLite drops tzinfo; everything we store is UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def asset_out(a: Asset) -> AssetOut:
    done = a.status == AssetStatus.COMPLETED.value
    return AssetOut(
        id=a.id,
        project_id=a.project_id,
        job_id=a.job_id,
        category=a.category,
        name=a.name,
        description=a.description,
        prompt=a.prompt,
        aspect_ratio=a.aspect_ratio,
        art_style=a.art_style,
        status=a.status,
        image_url=f"/api/v1/assets/{a.id}/image" if done else None,
        error=ErrorInfo(code=a.error_code, message=a.error_message or "") if a.error_code else None,
        created_at=_utc(a.created_at),
    )


def project_out(p: Project) -> ProjectOut:
    return ProjectOut(
        project_id=p.id,
        title=p.title,
        genre=p.genre,
        synopsis=p.synopsis,
        art_style=p.art_style,
        custom_art_notes=p.custom_art_notes,
        art_bible=ArtBible.model_validate(p.art_bible),
        blueprints=[AssetBlueprint.model_validate(b) for b in p.blueprints],
        model_used=p.model_used,
        created_at=_utc(p.created_at),
    )


def project_detail(p: Project, assets: list[Asset]) -> ProjectDetail:
    return ProjectDetail(**project_out(p).model_dump(), assets=[asset_out(a) for a in assets])


def job_out(j: Job, assets: list[Asset]) -> JobOut:
    return JobOut(
        job_id=j.id,
        project_id=j.project_id,
        status=j.status,
        total=j.total,
        completed=j.completed,
        failed=j.failed,
        assets=[asset_out(a) for a in assets],
        created_at=_utc(j.created_at),
        updated_at=_utc(j.updated_at),
    )
