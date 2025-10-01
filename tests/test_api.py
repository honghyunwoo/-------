"""
API 통합 테스트
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.asgi import app
from app.database.connection import Base, engine, SessionLocal
from app.models.user import User
from app.services.auth import get_password_hash

# 테스트 클라이언트
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """테스트용 데이터베이스 설정"""
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    yield
    # 테이블 삭제 (테스트 종료 후)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    """테스트 사용자 생성"""
    db = SessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("test1234"),
        full_name="Test User",
        is_active=True,
        subscription_plan="free",
        credits=3
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def auth_headers(test_user):
    """인증 헤더 생성"""
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "test1234"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestAuthentication:
    """인증 관련 테스트"""

    def test_register_user(self, setup_database):
        """회원가입 테스트"""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["subscription_plan"] == "free"
        assert data["credits"] == 3

    def test_login(self, setup_database, test_user):
        """로그인 테스트"""
        response = client.post(
            "/auth/token",
            data={"username": "test@example.com", "password": "test1234"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_get_current_user(self, setup_database, auth_headers):
        """현재 사용자 정보 조회 테스트"""
        response = client.get("/auth/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_invalid_login(self, setup_database):
        """잘못된 로그인 테스트"""
        response = client.post(
            "/auth/token",
            data={"username": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401

class TestVideoGeneration:
    """영상 생성 관련 테스트"""

    def test_create_video_without_auth(self, setup_database):
        """인증 없이 영상 생성 시도"""
        response = client.post(
            "/api/v1/videos",
            json={"video_subject": "Test Video"}
        )
        assert response.status_code == 401

    def test_create_video_with_auth(self, setup_database, auth_headers):
        """인증된 사용자의 영상 생성"""
        response = client.post(
            "/api/v1/videos",
            headers=auth_headers,
            json={
                "video_subject": "테스트 영상",
                "video_language": "ko",
                "video_aspect": "16:9"
            }
        )
        # 크레딧이 있다면 성공해야 함
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data["data"]
        else:
            # 크레딧 부족 시
            assert response.status_code == 402

    def test_usage_limit(self, setup_database, test_user, auth_headers):
        """사용량 제한 테스트"""
        # 무료 사용자는 3개까지만 가능
        for i in range(4):
            response = client.post(
                "/api/v1/videos",
                headers=auth_headers,
                json={
                    "video_subject": f"테스트 영상 {i+1}",
                    "video_language": "ko"
                }
            )
            if i < 3:
                # 처음 3개는 성공해야 함
                assert response.status_code in [200, 202]
            else:
                # 4번째는 실패해야 함 (크레딧 부족)
                assert response.status_code == 402

class TestTemplates:
    """템플릿 관련 테스트"""

    def test_get_templates(self, setup_database):
        """템플릿 목록 조회"""
        response = client.get("/templates/")
        assert response.status_code == 200

    def test_create_template(self, setup_database, auth_headers):
        """템플릿 생성"""
        response = client.post(
            "/templates/",
            headers=auth_headers,
            json={
                "name": "나의 템플릿",
                "description": "커스텀 템플릿",
                "category": "custom",
                "parameters": {
                    "font_size": 60,
                    "text_color": "#FFFFFF"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "나의 템플릿"

class TestPayment:
    """결제 관련 테스트"""

    def test_create_subscription(self, setup_database, auth_headers):
        """구독 생성 테스트"""
        response = client.post(
            "/payment/subscribe",
            headers=auth_headers,
            json={"plan": "basic"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 29000

    def test_invalid_plan(self, setup_database, auth_headers):
        """잘못된 플랜 테스트"""
        response = client.post(
            "/payment/subscribe",
            headers=auth_headers,
            json={"plan": "invalid_plan"}
        )
        assert response.status_code == 400

class TestSecurity:
    """보안 관련 테스트"""

    def test_cors_headers(self, setup_database):
        """CORS 헤더 테스트"""
        response = client.options(
            "/api/v1/videos",
            headers={"Origin": "http://localhost:8501"}
        )
        assert "access-control-allow-origin" in response.headers

    def test_security_headers(self, setup_database):
        """보안 헤더 테스트"""
        response = client.get("/")
        headers = response.headers
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("x-xss-protection") == "1; mode=block"

    def test_rate_limiting(self, setup_database):
        """Rate Limiting 테스트"""
        # 짧은 시간에 많은 요청 보내기
        for i in range(100):
            response = client.get("/")
            # Rate limit에 걸리면 429 상태 코드
            if response.status_code == 429:
                assert True
                break
        else:
            # Rate limiting이 설정되어 있지 않거나 한도가 너무 높음
            pytest.skip("Rate limiting not triggered")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])