#!/usr/bin/env python
"""
데이터베이스 초기화 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 모델 임포트
from app.database.connection import Base, engine
from app.models.user import User
from app.models.subscription import Subscription, Payment
from app.models.video_history import VideoHistory
from app.models.template import Template
from app.models.branding import Branding
from app.models.team import Team
from app.services.auth import get_password_hash

def create_database():
    """PostgreSQL 데이터베이스 생성"""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/postgres")

    # postgres 기본 데이터베이스에 연결
    temp_engine = create_engine(db_url.replace("/owl_studio", "/postgres"))

    with temp_engine.connect() as conn:
        # 자동 커밋 모드로 변경
        conn.execute(text("commit"))

        # 데이터베이스 존재 확인
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'owl_studio'")
        ).fetchone()

        if not exists:
            conn.execute(text("CREATE DATABASE owl_studio"))
            print("✅ 데이터베이스 'owl_studio' 생성 완료")
        else:
            print("ℹ️ 데이터베이스 'owl_studio'가 이미 존재합니다")

def create_tables():
    """모든 테이블 생성"""
    print("📊 테이블 생성 중...")

    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)

    print("✅ 모든 테이블 생성 완료")

def create_test_user():
    """테스트 사용자 생성"""
    from app.database.connection import SessionLocal

    db = SessionLocal()
    try:
        # 테스트 사용자 확인
        test_user = db.query(User).filter(User.email == "test@owl-studio.kr").first()

        if not test_user:
            # 테스트 사용자 생성
            test_user = User(
                email="test@owl-studio.kr",
                hashed_password=get_password_hash("test1234"),
                full_name="테스트 사용자",
                is_active=True,
                is_superuser=False,
                subscription_plan="free",
                credits=3
            )
            db.add(test_user)

            # 관리자 사용자 생성
            admin_user = User(
                email="admin@owl-studio.kr",
                hashed_password=get_password_hash("admin1234"),
                full_name="관리자",
                is_active=True,
                is_superuser=True,
                subscription_plan="business",
                credits=-1  # 무제한
            )
            db.add(admin_user)

            db.commit()
            print("✅ 테스트 사용자 생성 완료")
            print("   📧 일반: test@owl-studio.kr / test1234")
            print("   📧 관리자: admin@owl-studio.kr / admin1234")
        else:
            print("ℹ️ 테스트 사용자가 이미 존재합니다")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

def init_database():
    """데이터베이스 초기화 메인 함수"""
    print("\n🦉 올빼미 AI 영상 스튜디오 - 데이터베이스 초기화")
    print("=" * 50)

    try:
        # 1. 데이터베이스 생성
        create_database()

        # 2. 테이블 생성
        create_tables()

        # 3. 테스트 데이터 생성
        create_test_user()

        print("\n✅ 데이터베이스 초기화 완료!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 초기화 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()