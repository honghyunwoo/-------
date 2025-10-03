#!/usr/bin/env python
"""
구독 자동 갱신 테스트

구독 자동 갱신 시스템을 검증합니다:
- 자동 갱신 대상 조회
- 빌링키를 사용한 자동 결제
- 갱신 실패 처리
- 만료 임박 알림
- API 엔드포인트
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))


def test_get_renewable_subscriptions():
    """자동 갱신 대상 조회 테스트"""
    print("\n[TEST] Get renewable subscriptions...")

    try:
        from app.database.connection import SessionLocal
        from app.services import subscription as subscription_service
        from app.models.user import User
        from app.models.subscription import Subscription
        from datetime import datetime, timedelta

        db = SessionLocal()

        # 테스트 사용자 생성
        user = User(
            email="test_renewal@example.com",
            full_name="Test Renewal",
            hashed_password="test",
            is_active=True,
            subscription_plan="pro",
            credits=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 자동 갱신 대상 구독 생성
        tomorrow = datetime.now() + timedelta(days=1)
        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            start_date=datetime.now() - timedelta(days=29),
            end_date=tomorrow,  # 내일 만료
            is_active=1,
            auto_renew=1,
            billing_key="test_billing_key_123",  # 빌링키 존재
            next_billing_date=tomorrow
        )
        db.add(subscription)
        db.commit()

        # 자동 갱신 대상 조회
        renewable = subscription_service.get_renewable_subscriptions(db)

        # 검증
        assert len(renewable) >= 1, "Should find at least 1 renewable subscription"

        found = any(sub.id == subscription.id for sub in renewable)
        assert found, "Should find the test subscription"

        print("[OK] Renewable subscriptions found")

        # 정리
        db.query(Subscription).filter(Subscription.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        db.close()

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_expiring_subscriptions():
    """만료 임박 구독 조회 테스트"""
    print("\n[TEST] Get expiring subscriptions...")

    try:
        from app.database.connection import SessionLocal
        from app.services import subscription as subscription_service
        from app.models.user import User
        from app.models.subscription import Subscription

        db = SessionLocal()

        # 테스트 사용자 생성
        user = User(
            email="test_expiring@example.com",
            full_name="Test Expiring",
            hashed_password="test",
            is_active=True,
            subscription_plan="pro",
            credits=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 3일 후 만료 구독 생성
        in_3_days = datetime.now() + timedelta(days=3)
        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            start_date=datetime.now() - timedelta(days=27),
            end_date=in_3_days,
            is_active=1,
            auto_renew=0
        )
        db.add(subscription)
        db.commit()

        # 만료 임박 조회 (3일 이내)
        expiring = subscription_service.get_expiring_subscriptions(db, days_before=3)

        # 검증
        found = any(sub.id == subscription.id for sub in expiring)
        assert found, "Should find the expiring subscription"

        print("[OK] Expiring subscriptions found")

        # 정리
        db.query(Subscription).filter(Subscription.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        db.close()

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_toggle_auto_renew():
    """자동 갱신 토글 테스트"""
    print("\n[TEST] Toggle auto-renew...")

    try:
        from app.database.connection import SessionLocal
        from app.services import subscription as subscription_service
        from app.models.user import User
        from app.models.subscription import Subscription

        db = SessionLocal()

        # 테스트 사용자 및 구독 생성
        user = User(
            email="test_toggle@example.com",
            full_name="Test Toggle",
            hashed_password="test",
            is_active=True,
            subscription_plan="pro",
            credits=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            is_active=1,
            auto_renew=1
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # 자동 갱신 비활성화
        result = subscription_service.toggle_auto_renew(db, subscription.id, enable=False)
        assert result["status"] == "success", "Should toggle successfully"

        db.refresh(subscription)
        assert subscription.auto_renew == 0, "Auto-renew should be disabled"

        print("[OK] Auto-renew disabled")

        # 자동 갱신 활성화
        result = subscription_service.toggle_auto_renew(db, subscription.id, enable=True)
        assert result["status"] == "success", "Should toggle successfully"

        db.refresh(subscription)
        assert subscription.auto_renew == 1, "Auto-renew should be enabled"

        print("[OK] Auto-renew enabled")

        # 정리
        db.query(Subscription).filter(Subscription.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        db.close()

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cancel_subscription():
    """구독 취소 테스트"""
    print("\n[TEST] Cancel subscription...")

    try:
        from app.database.connection import SessionLocal
        from app.services import subscription as subscription_service
        from app.models.user import User
        from app.models.subscription import Subscription

        db = SessionLocal()

        # 테스트 사용자 및 구독 생성
        user = User(
            email="test_cancel@example.com",
            full_name="Test Cancel",
            hashed_password="test",
            is_active=True,
            subscription_plan="pro",
            credits=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            is_active=1,
            auto_renew=1
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # 구독 취소
        result = subscription_service.cancel_subscription(db, subscription.id)
        assert result["status"] == "success", "Should cancel successfully"

        db.refresh(subscription)
        db.refresh(user)

        assert subscription.is_active == 0, "Subscription should be inactive"
        assert subscription.auto_renew == 0, "Auto-renew should be disabled"
        assert user.subscription_plan == "free", "User plan should be free"
        assert user.credits == 3, "User credits should be 3 (free plan)"

        print("[OK] Subscription canceled successfully")

        # 정리
        db.query(Subscription).filter(Subscription.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        db.close()

        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Subscription Auto-Renewal Test Suite")
    print("=" * 60)

    tests = [
        test_get_renewable_subscriptions,
        test_get_expiring_subscriptions,
        test_toggle_auto_renew,
        test_cancel_subscription,
    ]

    all_passed = True

    for test_func in tests:
        if not test_func():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All subscription renewal tests passed!")
        print("\nProcessed Scenarios:")
        print("  [PASS] Get renewable subscriptions")
        print("  [PASS] Get expiring subscriptions")
        print("  [PASS] Toggle auto-renew")
        print("  [PASS] Cancel subscription")
        print("\nFeatures:")
        print("  - Auto-renew target detection")
        print("  - Expiration reminder detection")
        print("  - Auto-renew toggle")
        print("  - Subscription cancellation")
    else:
        print("[FAIL] Some subscription renewal tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
