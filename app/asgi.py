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

task_dir = utils.task_dir()
app.mount(
    "/tasks", StaticFiles(directory=task_dir, html=True, follow_symlink=True), name=""
)

public_dir = utils.public_dir()
app.mount("/", StaticFiles(directory=public_dir, html=True), name="")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("shutdown event")


@app.on_event("startup")
async def startup_event():
    logger.info("startup event")
    try:
        create_all_tables()
        logger.info("Database tables created.")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
