
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# 개발 환경에서는 SQLite, 프로덕션에서는 PostgreSQL
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # SQLite 사용 (개발 환경)
    DATABASE_URL = "sqlite:///./owl_studio.db"
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL 사용 (프로덕션)
    # 보안: DATABASE_URL 환경 변수 필수
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL environment variable is required for PostgreSQL. "
            "Please set it in your .env file. "
            "Example: DATABASE_URL=postgresql://user:password@localhost/dbname"
        )
    connect_args = {}

# 데이터베이스 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # SQL 로깅 비활성화
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 정의
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

