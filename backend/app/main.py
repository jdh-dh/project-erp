"""FastAPI 애플리케이션 엔트리포인트."""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    auth,
    change_logs,
    costs,
    customers,
    documents,
    hardware,
    issues,
    projects,
    releases,
    report,
    schedule,
    software,
    testing,
    users,
)
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("erp.api")


def create_app() -> FastAPI:
    app = FastAPI(title="개발 프로젝트 ERP API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning("AppError on %s %s: %s", request.method, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "서버 내부 오류가 발생했습니다.", "code": "INTERNAL_ERROR"},
        )

    @app.get("/api/health", tags=["health"])
    def health():
        return {"status": "ok"}

    for router in (
        auth.router,
        users.router,
        customers.router,
        projects.router,
        schedule.router,
        hardware.router,
        software.router,
        testing.router,
        issues.router,
        documents.router,
        releases.router,
        costs.router,
        report.router,
        change_logs.router,
    ):
        app.include_router(router, prefix="/api")

    return app


app = create_app()
