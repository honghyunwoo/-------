#!/usr/bin/env python
"""
인증 시스템 테스트 스크립트
회원가입, 로그인, JWT 토큰 검증 테스트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def test_password_hashing():
    """패스워드 해싱 테스트"""
    print("\n[TEST] Password hashing test...")

    try:
        from app.services.auth import get_password_hash, verify_password

        password = "test1234"
        hashed = get_password_hash(password)
        print(f"[OK] Password hashed: {hashed[:20]}...")

        # 검증
        is_valid = verify_password(password, hashed)
        if is_valid:
            print("[OK] Password verification successful")
        else:
            print("[FAIL] Password verification failed")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Password hashing test failed: {e}")
        return False

def test_jwt_token():
    """JWT 토큰 생성 및 검증 테스트"""
    print("\n[TEST] JWT token test...")

    try:
        from app.services.auth import create_access_token, verify_token
        from datetime import timedelta

        # 토큰 생성
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data, expires_delta=timedelta(minutes=15))
        print(f"[OK] Token created: {token[:20]}...")

        # 토큰 검증
        payload = verify_token(token)
        if payload and payload.get("sub") == "test@example.com":
            print("[OK] Token verification successful")
        else:
            print("[FAIL] Token verification failed")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] JWT token test failed: {e}")
        return False

def test_user_creation():
    """사용자 생성 테스트"""
    print("\n[TEST] User creation test...")

    try:
        from app.database.connection import SessionLocal
        from app.models import User
        from app.services.auth import get_password_hash

        db = SessionLocal()

        # 기존 테스트 사용자 삭제
        test_user = db.query(User).filter(User.email == "auth_test@example.com").first()
        if test_user:
            db.delete(test_user)
            db.commit()
            print("[INFO] Existing test user removed")

        # 새 사용자 생성
        new_user = User(
            email="auth_test@example.com",
            hashed_password=get_password_hash("test1234"),
            full_name="Auth Test User",
            is_active=True,
            subscription_plan="free",
            credits=3
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"[OK] User created with ID: {new_user.id}")

        # 사용자 조회 테스트
        found_user = db.query(User).filter(User.email == "auth_test@example.com").first()
        if found_user:
            print("[OK] User retrieval successful")
        else:
            print("[FAIL] User retrieval failed")
            db.close()
            return False

        db.close()
        return True

    except Exception as e:
        print(f"[FAIL] User creation test failed: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 50)
    print("Authentication System Test")
    print("=" * 50)

    all_passed = True

    # 1. 패스워드 해싱 테스트
    if not test_password_hashing():
        all_passed = False

    # 2. JWT 토큰 테스트
    if not test_jwt_token():
        all_passed = False

    # 3. 사용자 생성 테스트
    if not test_user_creation():
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("[SUCCESS] All authentication tests passed!")
    else:
        print("[FAIL] Some authentication tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()