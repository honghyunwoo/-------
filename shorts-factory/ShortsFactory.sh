#!/bin/bash
# Shorts Factory Launcher

cd "$(dirname "$0")"

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "Python3이 설치되어 있지 않습니다."
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
python3 gui_app.py &
