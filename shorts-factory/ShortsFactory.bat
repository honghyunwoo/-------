@echo off
title Shorts Factory
cd /d "%~dp0"

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 설치하세요.
    pause
    exit /b 1
)

REM 의존성 설치 확인
if not exist "venv" (
    echo 가상환경 생성 중...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM GUI 실행
echo Shorts Factory 시작 중...
pythonw gui_app.py

exit
