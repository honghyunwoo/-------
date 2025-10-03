"""Application implementation - ASGI."""

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
# Python 3.13 호환성 문제로 prometheus 제거
# from starlette_prometheus import PrometheusMiddleware, add_prometheus_middleware

from app.config import config
from app.database.models import create_all_tables
from app.models.exception import HttpException
from app.router import root_api_router
from app.utils import utils
from app.middleware.security import setup_security_middleware
from app.monitoring.sentry_config import init_sentry
from app.middleware.monitoring import (
    PerformanceMonitoringMiddleware,
    UserActivityMonitoringMiddleware,
)


def exception_handler(request: Request, e: HttpException):
    return JSONResponse(
        status_code=e.status_code,
        content=utils.get_response(e.status_code, e.data, e.message),
    )


def validation_exception_handler(request: Request, e: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=utils.get_response(
            status=400, data=e.errors(), message="field required"
        ),
    )


def get_application() -> FastAPI:
    """Initialize FastAPI application.

    Returns:
       FastAPI: Application object instance.

    """
    instance = FastAPI(
        title=config.project_name,
        description=config.project_description,
        version=config.project_version,
        debug=False,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "사용자 인증 및 회원가입 관련 API",
            },
            {
                "name": "Videos",
                "description": "AI 영상 생성 및 관리 API",
            },
            {
                "name": "Credits",
                "description": "크레딧 관리 및 사용 내역 API",
            },
            {
                "name": "Payment",
                "description": "결제 및 구독 관리 API",
            },
            {
                "name": "History",
                "description": "영상 생성 히스토리 조회 API",
            },
            {
                "name": "Templates",
                "description": "영상 템플릿 관리 API",
            },
            {
                "name": "Teams",
                "description": "팀 협업 기능 API",
            },
            {
                "name": "Health",
                "description": "시스템 상태 모니터링 API",
            },
        ],
        contact={
            "name": "올빼미 AI 영상 스튜디오",
            "url": "https://owl-studio.kr",
            "email": "support@owl-studio.kr",
        },
        license_info={
            "name": "Commercial License",
            "url": "https://owl-studio.kr/license",
        },
    )
    instance.include_router(root_api_router)
    instance.add_exception_handler(HttpException, exception_handler)
    instance.add_exception_handler(RequestValidationError, validation_exception_handler)
    # Prometheus middleware 제거 (Python 3.13 호환성)
    # instance.add_middleware(PrometheusMiddleware)
    return instance


app = get_application()

# 보안 미들웨어 설정
app = setup_security_middleware(app)

# 모니터링 미들웨어 추가
app.add_middleware(PerformanceMonitoringMiddleware)
app.add_middleware(UserActivityMonitoringMiddleware)

task_dir = utils.task_dir()
app.mount(
    "/tasks", StaticFiles(directory=task_dir, html=True, follow_symlink=True), name=""
)

public_dir = utils.public_dir()
app.mount("/", StaticFiles(directory=public_dir, html=True), name="")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("shutdown event")

    # 스케줄러 중지
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")


@app.on_event("startup")
async def startup_event():
    logger.info("startup event")

    # Sentry 초기화
    try:
        app_env = os.getenv("APP_ENV", "development")
        init_sentry(
            environment=app_env,
            traces_sample_rate=0.1 if app_env == "production" else 1.0,
            profiles_sample_rate=0.1 if app_env == "production" else 1.0,
        )
        logger.info(f"Sentry initialized for {app_env} environment")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")

    try:
        create_all_tables()
        logger.info("Database tables created.")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")

    # 자동 갱신 스케줄러 시작
    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
