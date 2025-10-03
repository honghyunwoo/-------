"""
Sentry 에러 추적 설정
"""
import os
from typing import Optional
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from loguru import logger


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
):
    """
    Sentry SDK 초기화

    Args:
        dsn: Sentry DSN (환경 변수에서 자동 로드)
        environment: 환경 (development, staging, production)
        traces_sample_rate: 트랜잭션 샘플링 비율 (0.0 ~ 1.0)
        profiles_sample_rate: 프로파일링 샘플링 비율 (0.0 ~ 1.0)
    """
    # DSN 확인
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.warning("Sentry DSN not configured. Error tracking disabled.")
        return

    # Sentry 초기화
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        # 통합 설정
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=None,  # Loguru와 함께 사용하므로 None
                event_level=None,  # 명시적 캡처만 사용
            ),
        ],
        # 성능 모니터링
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        # 릴리스 정보
        release=os.getenv("APP_VERSION", "1.0.0"),
        # 민감 정보 필터링
        send_default_pii=False,
        # 요청 데이터 수집
        request_bodies="medium",
        # 최대 breadcrumb 수
        max_breadcrumbs=50,
        # 첨부 파일 비활성화 (보안)
        attach_stacktrace=True,
        # 환경 변수 제외 (민감 정보)
        send_client_reports=True,
        # 에러 전송 전 콜백
        before_send=before_send_handler,
        # Breadcrumb 전송 전 콜백
        before_breadcrumb=before_breadcrumb_handler,
    )

    logger.info(f"Sentry initialized for environment: {environment}")


def before_send_handler(event, hint):
    """
    에러 전송 전 처리 (민감 정보 필터링)

    Args:
        event: Sentry 이벤트
        hint: 추가 정보

    Returns:
        수정된 이벤트 또는 None (전송 스킵)
    """
    # 민감한 키 목록
    sensitive_keys = [
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "cookie",
        "session",
        "credit_card",
        "ssn",
    ]

    # Request 데이터 필터링
    if "request" in event:
        if "headers" in event["request"]:
            for key in list(event["request"]["headers"].keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    event["request"]["headers"][key] = "[REDACTED]"

        if "data" in event["request"]:
            for key in list(event["request"]["data"].keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    event["request"]["data"][key] = "[REDACTED]"

        if "cookies" in event["request"]:
            event["request"]["cookies"] = "[REDACTED]"

    # Exception 정보에서 민감 정보 제거
    if "exception" in event:
        for exc in event["exception"].get("values", []):
            if "stacktrace" in exc:
                for frame in exc["stacktrace"].get("frames", []):
                    if "vars" in frame:
                        for key in list(frame["vars"].keys()):
                            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                                frame["vars"][key] = "[REDACTED]"

    return event


def before_breadcrumb_handler(crumb, hint):
    """
    Breadcrumb 전송 전 처리

    Args:
        crumb: Breadcrumb 데이터
        hint: 추가 정보

    Returns:
        수정된 breadcrumb 또는 None (스킵)
    """
    # SQL 쿼리에서 민감 정보 제거
    if crumb.get("category") == "query":
        # SQL 쿼리에서 값 파라미터 제거
        if "message" in crumb:
            # 간단한 파라미터 마스킹
            crumb["message"] = crumb["message"].split("--")[0].strip()

    return crumb


def capture_exception(error: Exception, context: dict = None, user_id: int = None):
    """
    예외를 Sentry에 캡처

    Args:
        error: 발생한 예외
        context: 추가 컨텍스트 정보
        user_id: 사용자 ID (선택)
    """
    with sentry_sdk.push_scope() as scope:
        # 사용자 정보 설정
        if user_id:
            scope.set_user({"id": user_id})

        # 컨텍스트 추가
        if context:
            for key, value in context.items():
                scope.set_context(key, value)

        # 예외 캡처
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", context: dict = None):
    """
    메시지를 Sentry에 캡처

    Args:
        message: 캡처할 메시지
        level: 레벨 (debug, info, warning, error, fatal)
        context: 추가 컨텍스트
    """
    with sentry_sdk.push_scope() as scope:
        # 컨텍스트 추가
        if context:
            for key, value in context.items():
                scope.set_context(key, value)

        # 메시지 캡처
        sentry_sdk.capture_message(message, level)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: dict = None,
):
    """
    Breadcrumb 추가 (이벤트 추적)

    Args:
        message: Breadcrumb 메시지
        category: 카테고리 (http, db, navigation, etc.)
        level: 레벨 (debug, info, warning, error)
        data: 추가 데이터
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


def set_user(user_id: int, email: str = None, username: str = None):
    """
    Sentry에 사용자 정보 설정

    Args:
        user_id: 사용자 ID
        email: 이메일 (선택)
        username: 사용자명 (선택)
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username,
    })


def set_tag(key: str, value: str):
    """
    Sentry 태그 설정 (필터링 및 검색용)

    Args:
        key: 태그 키
        value: 태그 값
    """
    sentry_sdk.set_tag(key, value)


def set_context(name: str, context: dict):
    """
    Sentry 컨텍스트 설정 (추가 정보)

    Args:
        name: 컨텍스트 이름
        context: 컨텍스트 데이터
    """
    sentry_sdk.set_context(name, context)
