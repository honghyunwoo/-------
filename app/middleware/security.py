"""
보안 미들웨어: CORS, Rate Limiting, Security Headers
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os


def get_user_identifier(request: Request) -> str:
    """
    사용자 식별자 추출 함수
    - 인증된 사용자: user_id 사용
    - 미인증 사용자: IP 주소 사용
    """
    # Authorization 헤더에서 사용자 정보 추출 시도
    auth_header = request.headers.get("Authorization", "")

    # 세션에 사용자 정보가 있으면 user_id 사용
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # JWT 토큰이 있으면 토큰 해시 사용 (파싱 실패 시 IP 사용)
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # 토큰의 일부만 사용 (전체 토큰은 너무 길어서)
        return f"token:{token[:20]}"

    # 기본: IP 주소 사용
    return f"ip:{get_remote_address(request)}"


# Rate Limiter 초기화
# IP 기반 기본 리미터
limiter = Limiter(key_func=get_remote_address)

# 사용자 기반 리미터 (인증된 요청용)
user_limiter = Limiter(key_func=get_user_identifier)

def setup_security_middleware(app: FastAPI):
    """보안 관련 미들웨어 설정"""

    # CORS 설정
    origins = [
        "http://localhost:8501",  # Streamlit
        "http://localhost:8080",  # FastAPI
        "http://localhost:3000",  # React 개발 서버
        "https://owl-studio.kr",  # 프로덕션 도메인
        "https://www.owl-studio.kr",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted Host 미들웨어
    if os.getenv("APP_ENV") == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["owl-studio.kr", "www.owl-studio.kr", "*.owl-studio.kr"]
        )

    # Rate Limiting 설정
    # IP 기반 리미터와 사용자 기반 리미터 모두 등록
    app.state.limiter = limiter
    app.state.user_limiter = user_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Security Headers 미들웨어
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    return app