
import unittest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.asgi import app
from app.database.connection import get_db, SessionLocal
from app.database.models import create_all_tables

# Use a separate test database
TEST_DATABASE_URL = "sqlite:///./test.db"

# This is a bit of a hack to override the DB for tests
# A better solution would use a fixture to manage the test DB
from app.database import connection
connection.DATABASE_URL = TEST_DATABASE_URL
engine = connection.create_engine(connection.DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = connection.sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Create tables for each test
        create_all_tables()

    def tearDown(self):
        # Drop tables after each test
        # This is simplified. A full solution would handle this more gracefully.
        import os
        if os.path.exists("./test.db"):
            os.remove("./test.db")

    def test_auth_flow(self):
        """Test user registration, login, and accessing a protected route."""
        # 1. Register a new user
        register_response = self.client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "testpassword", "full_name": "Test User"}
        )
        self.assertEqual(register_response.status_code, 200)
        user_data = register_response.json()
        self.assertEqual(user_data["email"], "test@example.com")

        # 2. Log in with the new user
        login_response = self.client.post(
            "/auth/token",
            data={"username": "test@example.com", "password": "testpassword"}
        )
        self.assertEqual(login_response.status_code, 200)
        token_data = login_response.json()
        self.assertIn("access_token", token_data)
        access_token = token_data["access_token"]

        # 3. Access a protected route
        me_response = self.client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(me_response.status_code, 200)
        me_data = me_response.json()
        self.assertEqual(me_data["email"], "test@example.com")

if __name__ == "__main__":
    unittest.main()
