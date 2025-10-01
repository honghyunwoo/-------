@echo off
chcp 65001 >nul
title 🦉 올빼미 AI 영상 스튜디오

echo.
echo ============================================
echo    🦉 올빼미 AI 영상 스튜디오 시작 중...
echo ============================================
echo.

:: Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo    https://www.python.org/ 에서 Python 3.10 이상을 설치해주세요.
    pause
    exit /b 1
)

:: 필요한 패키지 설치 확인
echo 📦 필요한 패키지 확인 중...
pip list | findstr "fastapi streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 필요한 패키지 설치 중...
    pip install -r requirements.txt
)

:: PostgreSQL 서비스 확인
echo 🗄️ PostgreSQL 서비스 확인 중...
sc query postgresql-x64-14 >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  PostgreSQL이 실행되지 않았습니다.
    echo    PostgreSQL을 먼저 시작해주세요.
    pause
)

:: FastAPI 서버 시작
echo.
echo 🚀 API 서버 시작 중...
start /min cmd /c "uvicorn app.asgi:application --host 0.0.0.0 --port 8080 --reload"
timeout /t 3 /nobreak >nul

:: Streamlit 앱 시작
echo 🎨 웹 인터페이스 시작 중...
start cmd /c "streamlit run webui/Main.py --server.port 8501"
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo    ✅ 올빼미 AI 영상 스튜디오 실행 완료!
echo ============================================
echo.
echo 🌐 웹 브라우저에서 다음 주소로 접속하세요:
echo    http://localhost:8501
echo.
echo 📚 API 문서:
echo    http://localhost:8080/docs
echo.
echo 종료하려면 이 창을 닫으세요.
echo ============================================
echo.

pause