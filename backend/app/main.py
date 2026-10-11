"""GameCraft AI - application factory, middleware and error handling."""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.ai.base import AIProvider
from app.ai.factory import build_provider
from app.api.v1 import router as v1_router
from app.config import Settings, get_settings
from app.db import Database
from app.errors import AppError
from app.ratelimit import RateLimiter
from app.service import GenerationService
from app.storage import Storage

logger = logging.getLogger("gamecraft")


def _error_response(request: Request, status_code: int, code: str, message: str, details=None, headers=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
        headers=headers,
    )


def create_app(settings: Settings | None = None, provider: AIProvider | None = None) -> FastAPI:
    """Build the app. `settings` / `provider` can be injected (tests, alternate backends)."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db = Database(settings.database_url)
        db.create_all()
        storage = Storage(settings.storage_dir)
        service = GenerationService(
            provider=provider or build_provider(settings),
            db=db,
            storage=storage,
            settings=settings,
        )
        service.recover_interrupted_work()
        app.state.settings = settings
        app.state.db = db
        app.state.service = service
        app.state.limiter = RateLimiter(settings.rate_limit_per_minute)
        logger.info("GameCraft API ready (env=%s, provider=%s)", settings.environment, service.provider.name)
        yield
        await service.shutdown()
        db.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
        description="Turn a game concept + art style into a cohesive set of game assets.",
        docs_url="/docs",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "Retry-After", "Content-Disposition"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        level = logging.ERROR if exc.status_code >= 500 and exc.status_code not in (502, 504) else logging.WARNING
        logger.log(level, "%s %s -> %s %s", request.method, request.url.path, exc.status_code, exc.code)
        headers = {"Retry-After": str(int(exc.retry_after))} if exc.retry_after else None
        return _error_response(request, exc.status_code, exc.code, exc.message, exc.details, headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(p) for p in err["loc"][1:]) or str(err["loc"][0]),
                "message": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ]
        return _error_response(request, 422, "VALIDATION_ERROR", "The request body or parameters are invalid.", details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        return _error_response(request, exc.status_code, codes.get(exc.status_code, f"HTTP_{exc.status_code}"), str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _error_response(request, 500, "INTERNAL_ERROR", "An unexpected error occurred.")

    app.include_router(v1_router)
    return app


app = create_app()
