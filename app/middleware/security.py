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

# Rate Limiter 초기화
limiter = Limiter(key_func=get_remote_address)

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
    app.state.limiter = limiter
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