"""
성능 모니터링 미들웨어
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from prometheus_client import Counter, Histogram, Gauge

# Prometheus 메트릭 정의
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests in progress",
    ["method", "endpoint"],
)

SLOW_REQUEST_COUNT = Counter(
    "http_slow_requests_total",
    "Total slow HTTP requests (>2s)",
    ["method", "endpoint"],
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0],
)

ACTIVE_USERS = Gauge(
    "active_users_total",
    "Number of active users",
)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """성능 모니터링 미들웨어"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        요청 처리 시간 측정 및 로깅

        Args:
            request: FastAPI Request
            call_next: 다음 미들웨어/핸들러

        Returns:
            Response: 응답
        """
        # 시작 시간 기록
        start_time = time.time()

        # 엔드포인트 추출
        endpoint = request.url.path
        method = request.method

        # 진행 중인 요청 증가
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        # Breadcrumb 추가 (Sentry)
        try:
            from app.monitoring.sentry_config import add_breadcrumb

            add_breadcrumb(
                message=f"{method} {endpoint}",
                category="http",
                level="info",
                data={
                    "url": str(request.url),
                    "method": method,
                    "client_host": request.client.host if request.client else None,
                },
            )
        except ImportError:
            pass

        # 요청 처리
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # 에러 발생 시
            status_code = 500
            logger.exception(f"Request failed: {method} {endpoint}")

            # Sentry에 에러 캡처
            try:
                from app.monitoring.sentry_config import capture_exception

                capture_exception(
                    e,
                    context={
                        "request": {
                            "method": method,
                            "url": str(request.url),
                            "headers": dict(request.headers),
                        }
                    },
                )
            except ImportError:
                pass

            raise

        finally:
            # 처리 시간 계산
            process_time = time.time() - start_time

            # 진행 중인 요청 감소
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

            # 메트릭 기록
            REQUEST_COUNT.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()

            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(
                process_time
            )

            # 느린 요청 감지 (2초 이상)
            if process_time > 2.0:
                SLOW_REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
                logger.warning(
                    f"Slow request detected: {method} {endpoint} "
                    f"({process_time:.2f}s) - Status: {status_code}"
                )

            # 응답 헤더에 처리 시간 추가
            response.headers["X-Process-Time"] = str(process_time)

            # 로깅 (INFO 레벨)
            logger.info(
                f"{method} {endpoint} - {status_code} - {process_time:.3f}s"
            )

        return response


class UserActivityMonitoringMiddleware(BaseHTTPMiddleware):
    """사용자 활동 모니터링 미들웨어"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        사용자 활동 추적

        Args:
            request: FastAPI Request
            call_next: 다음 미들웨어/핸들러

        Returns:
            Response: 응답
        """
        # 사용자 정보 추출 (인증된 경우)
        user = getattr(request.state, "user", None)

        if user:
            # Sentry에 사용자 설정
            try:
                from app.monitoring.sentry_config import set_user

                set_user(
                    user_id=user.id,
                    email=user.email if hasattr(user, "email") else None,
                )
            except ImportError:
                pass

            # 로깅
            logger.debug(
                f"User activity: user_id={user.id}, "
                f"endpoint={request.url.path}, method={request.method}"
            )

        # 요청 처리
        response = await call_next(request)

        return response


def log_db_query(query_type: str, duration: float):
    """
    데이터베이스 쿼리 로깅 및 메트릭 기록

    Args:
        query_type: 쿼리 타입 (SELECT, INSERT, UPDATE, DELETE)
        duration: 실행 시간 (초)
    """
    DB_QUERY_DURATION.labels(query_type=query_type).observe(duration)

    if duration > 1.0:
        logger.warning(
            f"Slow database query detected: {query_type} ({duration:.3f}s)"
        )
    else:
        logger.debug(f"Database query: {query_type} ({duration:.3f}s)")


def update_active_users(count: int):
    """
    활성 사용자 수 업데이트

    Args:
        count: 활성 사용자 수
    """
    ACTIVE_USERS.set(count)
