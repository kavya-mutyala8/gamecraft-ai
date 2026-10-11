"""HTTP surface: /api/v1."""

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import FileResponse

from app.ai.prompts import STYLE_LABELS
from app.ratelimit import enforce_rate_limit
from app.schemas import (
    ArtStyleEnum,
    AspectRatioEnum,
    AssetCategoryEnum,
    AssetGenerateRequest,
    AssetOut,
    BatchGenerateRequest,
    CatalogResponse,
    EngineTarget,
    ErrorResponse,
    GameConceptRequest,
    HealthResponse,
    JobOut,
    ProjectDetail,
    ProjectOut,
    RegenerateRequest,
    StyleInfo,
)
from app.service import GenerationService

router = APIRouter(prefix="/api/v1")

_ERRORS = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Conflict with current state"},
    422: {"model": ErrorResponse, "description": "Invalid request or content blocked by the AI provider"},
    429: {"model": ErrorResponse, "description": "Rate limited"},
    502: {"model": ErrorResponse, "description": "AI provider failure"},
    504: {"model": ErrorResponse, "description": "AI provider timeout"},
}


def get_service(request: Request) -> GenerationService:
    return request.app.state.service


# ------------------------------------------------------------------ system
@router.get("/health", response_model=HealthResponse, tags=["System"])
def health(request: Request, response: Response):
    """Liveness + dependency status. Returns 503 if the database is unreachable."""
    st = request.app.state
    db_ok = st.db.ping()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version=st.settings.api_version,
        service=st.settings.app_name,
        provider=st.service.provider.name,
        thinking_model=st.settings.thinking_model,
        image_model=st.settings.image_model,
        database="ok" if db_ok else "unreachable",
    )


@router.get("/catalog", response_model=CatalogResponse, tags=["System"])
def catalog(request: Request):
    """Everything the frontend needs to render its pickers."""
    return CatalogResponse(
        art_styles=[StyleInfo(id=s, label=STYLE_LABELS[s]) for s in ArtStyleEnum],
        categories=list(AssetCategoryEnum),
        aspect_ratios=list(AspectRatioEnum),
        engine_targets=list(EngineTarget),
        max_batch_size=request.app.state.settings.max_batch_size,
    )


# ------------------------------------------------------------------ concept
@router.post(
    "/analyze",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Concept"],
    summary="Turn a game concept into a project with an Art Bible and asset blueprints",
    responses={k: _ERRORS[k] for k in (422, 429, 502, 504)},
    dependencies=[Depends(enforce_rate_limit)],
)
async def analyze(body: GameConceptRequest, service: GenerationService = Depends(get_service)):
    return await service.analyze(body)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectDetail,
    tags=["Concept"],
    responses={404: _ERRORS[404]},
)
def get_project(project_id: str, service: GenerationService = Depends(get_service)):
    """Project, Art Bible, blueprints and every asset generated so far."""
    return service.get_project_detail(project_id)


# --------------------------------------------------------------- generation
@router.post(
    "/generate/single",
    response_model=AssetOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Generation"],
    summary="Generate one asset (synchronous)",
    responses={k: _ERRORS[k] for k in (404, 422, 429, 502, 504)},
    dependencies=[Depends(enforce_rate_limit)],
)
async def generate_single(body: AssetGenerateRequest, service: GenerationService = Depends(get_service)):
    return await service.generate_single(body)


@router.post(
    "/generate/batch",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Generation"],
    summary="Start generating a full asset pack (asynchronous job)",
    description="Returns immediately with a job. Poll `GET /jobs/{job_id}` until `status` is "
    "`completed`, `partial` or `failed`. Omit `blueprints` to use the ones from `/analyze`.",
    responses={k: _ERRORS[k] for k in (404, 409, 422, 429)},
    dependencies=[Depends(enforce_rate_limit)],
)
async def generate_batch(body: BatchGenerateRequest, service: GenerationService = Depends(get_service)):
    return await service.start_batch(body)


@router.get("/jobs/{job_id}", response_model=JobOut, tags=["Generation"], responses={404: _ERRORS[404]})
def get_job(job_id: str, service: GenerationService = Depends(get_service)):
    return service.get_job(job_id)


# ------------------------------------------------------------------- assets
@router.get("/assets/{asset_id}", response_model=AssetOut, tags=["Assets"], responses={404: _ERRORS[404]})
def get_asset(asset_id: str, service: GenerationService = Depends(get_service)):
    return service.get_asset(asset_id)


@router.get(
    "/assets/{asset_id}/image",
    tags=["Assets"],
    summary="Download the generated image",
    response_class=FileResponse,
    responses={404: _ERRORS[404], 409: _ERRORS[409]},
)
def get_asset_image(asset_id: str, service: GenerationService = Depends(get_service)):
    path, mime = service.get_asset_file(asset_id)
    return FileResponse(path, media_type=mime, headers={"Cache-Control": "public, max-age=31536000, immutable"})


@router.post(
    "/assets/{asset_id}/regenerate",
    response_model=AssetOut,
    tags=["Assets"],
    summary="Re-run generation for an asset (optionally with a new seed)",
    responses={k: _ERRORS[k] for k in (404, 409, 422, 429, 502, 504)},
    dependencies=[Depends(enforce_rate_limit)],
)
async def regenerate(
    asset_id: str,
    body: RegenerateRequest | None = None,
    service: GenerationService = Depends(get_service),
):
    return await service.regenerate(asset_id, body.seed if body else None)


# ------------------------------------------------------------------- export
@router.get(
    "/projects/{project_id}/export",
    tags=["Export"],
    summary="Download completed assets + manifest.json as a ZIP laid out for a game engine",
    response_class=Response,
    responses={404: _ERRORS[404], 409: _ERRORS[409]},
)
def export_project(
    project_id: str,
    engine: EngineTarget = Query(EngineTarget.UNIVERSAL),
    service: GenerationService = Depends(get_service),
):
    data, filename = service.build_export_zip(project_id, engine)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
