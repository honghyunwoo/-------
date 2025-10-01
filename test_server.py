#!/usr/bin/env python
"""
서버 테스트 스크립트
데이터베이스 초기화 및 FastAPI 서버 실행
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_imports():
    """모든 임포트 테스트"""
    print("[TEST] Import test starting...")

    try:
        from app.database.connection import engine, Base
        print("[OK] Database connection module imported")
    except Exception as e:
        print(f"[FAIL] Database connection module import failed: {e}")
        return False

    try:
        from app.models import User, Subscription, Payment
        print("[OK] Models imported")
    except Exception as e:
        print(f"[FAIL] Model import failed: {e}")
        return False

    try:
        from app.asgi import app
        print("[OK] FastAPI app imported")
    except Exception as e:
        print(f"[FAIL] FastAPI app import failed: {e}")
        return False

    return True

def create_tables():
    """데이터베이스 테이블 생성"""
    print("\n[DB] Creating database tables...")

    try:
        from app.database.models import create_all_tables
        create_all_tables()
        return True
    except Exception as e:
        print(f"[FAIL] Table creation failed: {e}")
        return False

def create_test_user():
    """테스트 사용자 생성"""
    print("\n[USER] Creating test user...")

    try:
        from app.database.connection import SessionLocal
        from app.models import User
        from app.services.auth import get_password_hash

        db = SessionLocal()

        # 기존 테스트 사용자 확인
        test_user = db.query(User).filter(User.email == "test@example.com").first()

        if not test_user:
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("test1234"),
                full_name="테스트 사용자",
                is_active=True,
                subscription_plan="free",
                credits=3
            )
            db.add(test_user)
            db.commit()
            print("[OK] Test user created")
            print("   Email: test@example.com")
            print("   Password: test1234")
        else:
            print("[INFO] Test user already exists")

        db.close()
        return True

    except Exception as e:
        print(f"[FAIL] User creation failed: {e}")
        return False

def run_server():
    """FastAPI 서버 실행"""
    print("\n[SERVER] Starting FastAPI server...")
    print("   주소: http://localhost:8080")
    print("   API 문서: http://localhost:8080/docs")
    print("   종료: Ctrl+C")

    try:
        import uvicorn
        uvicorn.run(
            "app.asgi:app",
            host="0.0.0.0",
            port=8080,
            reload=True
        )
    except Exception as e:
        print(f"[FAIL] Server start failed: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 50)
    print("OWL AI Video Studio - Server Test")
    print("=" * 50)

    # 1. 임포트 테스트
    if not test_imports():
        print("\n[FAIL] Import test failed. Check dependencies.")
        sys.exit(1)

    # 2. 테이블 생성
    if not create_tables():
        print("\n[FAIL] Table creation failed.")
        sys.exit(1)

    # 3. 테스트 사용자 생성
    if not create_test_user():
        print("\n[WARN] Test user creation failed (server will still run)")

    # 4. 서버 실행
    print("\n" + "=" * 50)
    run_server()

if __name__ == "__main__":
    main()