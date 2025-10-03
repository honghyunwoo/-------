"""성능 모니터링 및 APM (Application Performance Monitoring) 시스템"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import psutil
from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.user import User
from app.models.video import Video
from app.models.payment import Payment
from app.utils.cache import get_cache_stats

router = APIRouter()


def get_system_metrics() -> Dict:
    """시스템 리소스 메트릭 수집"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": disk.percent,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {}


def get_database_metrics(db: Session) -> Dict:
    """데이터베이스 메트릭 수집"""
    try:
        # 테이블별 레코드 수
        user_count = db.query(func.count(User.id)).scalar()
        video_count = db.query(func.count(Video.id)).scalar()
        payment_count = db.query(func.count(Payment.id)).scalar()

        # 데이터베이스 크기 (SQLite)
        try:
            db_size_result = db.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")).fetchone()
            db_size_mb = round(db_size_result[0] / (1024 * 1024), 2) if db_size_result else 0
        except:
            db_size_mb = 0

        return {
            "tables": {
                "users": user_count,
                "videos": video_count,
                "payments": payment_count,
            },
            "size_mb": db_size_mb,
        }
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        return {}


def get_application_metrics(db: Session) -> Dict:
    """애플리케이션 비즈니스 메트릭 수집"""
    try:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        # 활성 사용자
        active_users_24h = (
            db.query(func.count(func.distinct(User.id)))
            .filter(User.last_login >= last_24h)
            .scalar()
        )

        # 영상 생성 통계
        videos_24h = (
            db.query(func.count(Video.id))
            .filter(Video.created_at >= last_24h)
            .scalar()
        )

        videos_7d = (
            db.query(func.count(Video.id))
            .filter(Video.created_at >= last_7d)
            .scalar()
        )

        # 결제 통계
        payments_24h = (
            db.query(func.count(Payment.id))
            .filter(Payment.created_at >= last_24h)
            .scalar()
        )

        revenue_24h = (
            db.query(func.sum(Payment.amount))
            .filter(Payment.created_at >= last_24h, Payment.status == "done")
            .scalar()
            or 0
        )

        return {
            "users": {
                "active_24h": active_users_24h,
            },
            "videos": {
                "created_24h": videos_24h,
                "created_7d": videos_7d,
            },
            "payments": {
                "count_24h": payments_24h,
                "revenue_24h": float(revenue_24h),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get application metrics: {e}")
        return {}


@router.get("/api/monitoring/dashboard", tags=["Monitoring"])
def get_performance_dashboard(db: Session = Depends(get_db)):
    """통합 성능 대시보드 데이터 조회

    시스템, 데이터베이스, 애플리케이션 메트릭을 종합하여 반환합니다.
    """
    start_time = time.time()

    dashboard_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "system": get_system_metrics(),
        "database": get_database_metrics(db),
        "application": get_application_metrics(db),
        "response_time_ms": 0,  # 아래에서 계산
    }

    response_time = (time.time() - start_time) * 1000
    dashboard_data["response_time_ms"] = round(response_time, 2)

    logger.info(
        f"Performance dashboard generated in {response_time:.2f}ms"
    )

    return dashboard_data


@router.get("/api/monitoring/system", tags=["Monitoring"])
def get_system_info():
    """시스템 리소스 정보 조회"""
    return get_system_metrics()


@router.get("/api/monitoring/database", tags=["Monitoring"])
def get_database_info(db: Session = Depends(get_db)):
    """데이터베이스 정보 조회"""
    return get_database_metrics(db)


@router.get("/api/monitoring/application", tags=["Monitoring"])
def get_application_info(db: Session = Depends(get_db)):
    """애플리케이션 비즈니스 메트릭 조회"""
    return get_application_metrics(db)


@router.get("/api/monitoring/health/detailed", tags=["Monitoring"])
def detailed_health_check(db: Session = Depends(get_db)):
    """상세 헬스 체크

    시스템, 데이터베이스, 외부 서비스 상태를 종합적으로 확인합니다.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # 데이터베이스 체크
    try:
        db.execute(text("SELECT 1")).fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }

    # 디스크 공간 체크
    try:
        disk = psutil.disk_usage("/")
        disk_healthy = disk.percent < 90
        health_status["checks"]["disk"] = {
            "status": "healthy" if disk_healthy else "warning",
            "usage_percent": disk.percent,
            "message": (
                "Disk space OK"
                if disk_healthy
                else f"Disk usage high: {disk.percent}%"
            ),
        }
        if not disk_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unknown",
            "message": f"Failed to check disk: {str(e)}",
        }

    # 메모리 체크
    try:
        memory = psutil.virtual_memory()
        memory_healthy = memory.percent < 90
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory_healthy else "warning",
            "usage_percent": memory.percent,
            "message": (
                "Memory OK"
                if memory_healthy
                else f"Memory usage high: {memory.percent}%"
            ),
        }
        if not memory_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "message": f"Failed to check memory: {str(e)}",
        }

    return health_status


@router.get("/api/monitoring/slow-queries", tags=["Monitoring"])
def get_slow_queries(
    limit: int = 10, min_duration_ms: float = 100, db: Session = Depends(get_db)
):
    """느린 쿼리 조회 (로그 파일 기반)

    Args:
        limit: 반환할 최대 쿼리 수
        min_duration_ms: 최소 쿼리 시간 (밀리초)
    """
    # TODO: 실제 구현은 로그 파싱 또는 DB 쿼리 로그 분석 필요
    # 현재는 예시 데이터 반환
    return {
        "message": "Slow query tracking will be implemented with query logging",
        "min_duration_ms": min_duration_ms,
        "limit": limit,
        "queries": [],
    }


@router.get("/api/monitoring/errors/summary", tags=["Monitoring"])
def get_error_summary(hours: int = 24):
    """에러 요약 통계 (로그 파일 기반)

    Args:
        hours: 조회할 시간 범위 (시간)
    """
    # TODO: 실제 구현은 로그 파싱 필요
    # 현재는 Sentry를 통한 에러 추적 권장
    return {
        "message": "Error tracking is available through Sentry dashboard",
        "hours": hours,
        "recommendation": "Visit Sentry for detailed error analytics",
    }


@router.get("/api/monitoring/cache/stats", tags=["Monitoring"])
def get_redis_cache_stats():
    """Redis 캐시 통계 조회

    캐시 히트율, 총 키 개수 등 캐시 성능 지표를 반환합니다.
    """
    return get_cache_stats()
