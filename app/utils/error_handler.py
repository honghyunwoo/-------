"""
통합 에러 처리 유틸리티
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from loguru import logger


class APIError(HTTPException):
    """기본 API 에러 클래스"""

    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.error_code = error_code
        detail = {
            "message": message,
            "error_code": error_code or f"ERR_{status_code}",
        }
        if details:
            detail["details"] = details

        super().__init__(status_code=status_code, detail=detail)
        logger.error(
            f"API Error: {status_code} - {message} | Code: {error_code} | Details: {details}"
        )


class ValidationError(APIError):
    """입력 검증 에러"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            details=details,
            error_code="VALIDATION_ERROR",
        )


class AuthenticationError(APIError):
    """인증 에러"""

    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(APIError):
    """권한 에러"""

    def __init__(self, message: str = "접근 권한이 없습니다"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="AUTHORIZATION_ERROR",
        )


class NotFoundError(APIError):
    """리소스를 찾을 수 없음"""

    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource}를 찾을 수 없습니다"
        if resource_id:
            message += f" (ID: {resource_id})"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            details={"resource": resource, "resource_id": resource_id},
            error_code="NOT_FOUND",
        )


class InsufficientCreditsError(APIError):
    """크레딧 부족 에러"""

    def __init__(self, current: int, required: int):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            message=f"크레딧이 부족합니다. 현재: {current}개, 필요: {required}개",
            details={"current_credits": current, "required_credits": required},
            error_code="INSUFFICIENT_CREDITS",
        )


class RateLimitError(APIError):
    """Rate Limit 초과 에러"""

    def __init__(self, retry_after: Optional[int] = None):
        message = "요청 횟수 제한을 초과했습니다"
        if retry_after:
            message += f". {retry_after}초 후 다시 시도해주세요"

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            details={"retry_after": retry_after} if retry_after else None,
            error_code="RATE_LIMIT_EXCEEDED",
        )


class ServiceUnavailableError(APIError):
    """서비스 이용 불가 에러"""

    def __init__(self, service: str, reason: Optional[str] = None):
        message = f"{service} 서비스를 일시적으로 이용할 수 없습니다"
        if reason:
            message += f": {reason}"

        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            details={"service": service, "reason": reason},
            error_code="SERVICE_UNAVAILABLE",
        )


class ExternalAPIError(APIError):
    """외부 API 호출 에러"""

    def __init__(self, api_name: str, status_code: int, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=f"{api_name} API 호출 실패: {message}",
            details={"api_name": api_name, "api_status_code": status_code},
            error_code="EXTERNAL_API_ERROR",
        )


class DatabaseError(APIError):
    """데이터베이스 에러"""

    def __init__(self, operation: str, details: Optional[str] = None):
        message = f"데이터베이스 {operation} 작업 중 오류가 발생했습니다"
        if details:
            message += f": {details}"

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            details={"operation": operation, "error_details": details},
            error_code="DATABASE_ERROR",
        )


def handle_unexpected_error(error: Exception, context: str = "") -> APIError:
    """
    예상치 못한 에러를 처리하고 로깅

    Args:
        error: 발생한 예외
        context: 에러 발생 컨텍스트

    Returns:
        APIError: 일관된 형식의 API 에러
    """
    logger.exception(f"Unexpected error in {context}: {str(error)}")

    return APIError(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        details={"context": context, "error_type": type(error).__name__},
        error_code="INTERNAL_SERVER_ERROR",
    )


def log_error(error: Exception, context: str = "", user_id: Optional[int] = None):
    """
    에러 로깅 헬퍼 함수

    Args:
        error: 발생한 예외
        context: 에러 발생 컨텍스트
        user_id: 사용자 ID (선택)
    """
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
    }
    if user_id:
        log_data["user_id"] = user_id

    logger.error(f"Error occurred: {log_data}")
