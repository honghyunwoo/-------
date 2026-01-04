#!/bin/bash
# Shorts Factory Launcher for macOS
# .command 파일은 더블클릭으로 실행 가능

cd "$(dirname "$0")"

# Python 확인
if ! command -v python3 &> /dev/null; then
    osascript -e 'display alert "Python3이 설치되어 있지 않습니다." message "https://www.python.org/downloads/ 에서 Python을 설치하세요."'
    exit 1
fi

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# GUI 실행
echo "Shorts Factory 시작 중..."
python3 gui_app.py
