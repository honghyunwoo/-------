#!/usr/bin/env python
"""
FastAPI 서버 실행 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def main():
    """메인 함수"""
    print("=" * 50)
    print("OWL AI Video Studio - Server Starting")
    print("=" * 50)
    print("")
    print("Server URL: http://localhost:8080")
    print("API Docs:  http://localhost:8080/docs")
    print("Admin UI:  http://localhost:8080/admin")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:
        import uvicorn
        from app.asgi import app

        # 서버 실행
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8080,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"[ERROR] Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()