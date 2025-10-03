"""
Rate Limiting 테스트
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.asgi import app
from app.database.connection import get_db
from app.models.user import User
from app.services import auth as auth_service


client = TestClient(app)


def test_login_rate_limit():
    """로그인 Rate Limit 테스트 (분당 10회 제한)"""
    # 같은 IP에서 11회 로그인 시도
    for i in range(11):
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        if i < 10:
            # 처음 10회는 성공 (실패하더라도 429가 아님)
            assert response.status_code in [401, 400, 200]  # 인증 실패 또는 성공
        else:
            # 11번째는 Rate Limit 초과
            assert response.status_code == 429  # Too Many Requests


def test_register_rate_limit():
    """회원가입 Rate Limit 테스트 (시간당 5회 제한)"""
    # 같은 IP에서 6회 회원가입 시도
    for i in range(6):
        response = client.post(
            "/auth/register",
            json={
                "email": f"test{i}@example.com",
                "password": "password123",
                "full_name": f"Test User {i}",
            },
        )
        if i < 5:
            # 처음 5회는 성공 (중복 이메일이면 400)
            assert response.status_code in [201, 400]
        else:
            # 6번째는 Rate Limit 초과
            assert response.status_code == 429  # Too Many Requests


def test_credit_usage():
    """크레딧 사용 테스트"""
    # 테스트 사용자 생성
    from app.database.connection import SessionLocal

    db = SessionLocal()

    # 기존 테스트 사용자 삭제
    db.query(User).filter(User.email == "credit_test@example.com").delete()
    db.commit()

    # 새 사용자 생성
    user = User(
        email="credit_test@example.com",
        hashed_password=auth_service.get_password_hash("password123"),
        full_name="Credit Test User",
        is_verified=True,
        credits=3,  # 초기 크레딧 3개
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 로그인
    login_response = client.post(
        "/auth/login",
        json={"email": "credit_test@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 크레딧 잔액 조회
    balance_response = client.get(
        "/credits/balance", headers={"Authorization": f"Bearer {token}"}
    )
    assert balance_response.status_code == 200
    assert balance_response.json()["credits"] == 3

    # 크레딧 부족 테스트를 위해 크레딧을 0으로 설정
    user.credits = 0
    db.commit()

    # 크레딧 없이 영상 생성 시도 (실패해야 함)
    # 실제 영상 생성은 시간이 오래 걸리므로, 크레딧 체크만 테스트
    from app.services import usage

    with pytest.raises(Exception) as exc_info:
        usage.check_credits(db, user, required_credits=1)

    # 402 Payment Required 예외 확인
    assert "402" in str(exc_info.value) or "Not enough credits" in str(exc_info.value)

    # 정리
    db.delete(user)
    db.commit()
    db.close()


def test_credit_history():
    """크레딧 히스토리 테스트"""
    from app.database.connection import SessionLocal
    from app.services import usage

    db = SessionLocal()

    # 기존 테스트 사용자 삭제
    db.query(User).filter(User.email == "history_test@example.com").delete()
    db.commit()

    # 새 사용자 생성
    user = User(
        email="history_test@example.com",
        hashed_password=auth_service.get_password_hash("password123"),
        full_name="History Test User",
        is_verified=True,
        credits=10,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 크레딧 사용 (히스토리 기록)
    usage.use_credits(
        db=db,
        user=user,
        required_credits=2,
        action_type="video_generation",
        description="Test video generation",
        related_id="task_123",
    )

    # 크레딧 사용 후 잔액 확인
    db.refresh(user)
    assert user.credits == 8

    # 히스토리 조회
    history = usage.get_credit_history(db=db, user_id=user.id, skip=0, limit=10)
    assert len(history) > 0
    assert history[0].amount == -2
    assert history[0].balance_after == 8
    assert history[0].action_type == "video_generation"

    # 크레딧 추가 (히스토리 기록)
    usage.add_credits(
        db=db,
        user=user,
        credits=5,
        action_type="admin_grant",
        description="Admin granted credits",
    )

    # 크레딧 추가 후 잔액 확인
    db.refresh(user)
    assert user.credits == 13

    # 정리
    db.delete(user)
    db.commit()
    db.close()


if __name__ == "__main__":
    print("Running Rate Limiting Tests...")

    try:
        print("\n[TEST 1] Login Rate Limit")
        test_login_rate_limit()
        print("[PASS] Login rate limit working")
    except AssertionError as e:
        print(f"[FAIL] Login rate limit test failed: {e}")

    try:
        print("\n[TEST 2] Register Rate Limit")
        test_register_rate_limit()
        print("[PASS] Register rate limit working")
    except AssertionError as e:
        print(f"[FAIL] Register rate limit test failed: {e}")

    try:
        print("\n[TEST 3] Credit Usage")
        test_credit_usage()
        print("[PASS] Credit usage working")
    except Exception as e:
        print(f"[FAIL] Credit usage test failed: {e}")

    try:
        print("\n[TEST 4] Credit History")
        test_credit_history()
        print("[PASS] Credit history working")
    except Exception as e:
        print(f"[FAIL] Credit history test failed: {e}")

    print("\n[SUCCESS] All tests completed!")
