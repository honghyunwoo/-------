#!/usr/bin/env python
"""
간단한 FastAPI 테스트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

print("[1] Starting simple test...")

try:
    print("[2] Importing config...")
    from app.config.config import config
    print("[3] Config imported successfully")

    print("[4] Importing database...")
    from app.database.connection import engine, Base
    print("[5] Database imported successfully")

    print("[6] Importing models...")
    from app.models import User
    print("[7] Models imported successfully")

    print("[8] Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("[9] Tables created successfully")

    print("[10] Importing FastAPI app...")
    from app.asgi import app
    print("[11] FastAPI app imported successfully")

    print("\n[SUCCESS] All imports and setup completed!")

except Exception as e:
    print(f"\n[ERROR] Failed at step: {e}")
    import traceback
    traceback.print_exc()