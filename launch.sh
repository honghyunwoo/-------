#!/bin/bash

echo ""
echo "============================================"
echo "   🦉 올빼미 AI 영상 스튜디오 시작 중..."
echo "============================================"
echo ""

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python이 설치되지 않았습니다."
    echo "   https://www.python.org/ 에서 Python 3.10 이상을 설치해주세요."
    exit 1
fi

# 필요한 패키지 설치 확인
echo "📦 필요한 패키지 확인 중..."
if ! pip list | grep -q "fastapi\|streamlit"; then
    echo "📦 필요한 패키지 설치 중..."
    pip install -r requirements.txt
fi

# PostgreSQL 서비스 확인
echo "🗄️ PostgreSQL 서비스 확인 중..."
if ! systemctl is-active --quiet postgresql; then
    echo "⚠️  PostgreSQL이 실행되지 않았습니다."
    echo "   PostgreSQL을 먼저 시작해주세요."
    echo "   sudo systemctl start postgresql"
fi

# FastAPI 서버 시작
echo ""
echo "🚀 API 서버 시작 중..."
nohup uvicorn app.asgi:application --host 0.0.0.0 --port 8080 --reload > api.log 2>&1 &
API_PID=$!
sleep 3

# Streamlit 앱 시작
echo "🎨 웹 인터페이스 시작 중..."
nohup streamlit run webui/Main.py --server.port 8501 > ui.log 2>&1 &
UI_PID=$!
sleep 3

echo ""
echo "============================================"
echo "   ✅ 올빼미 AI 영상 스튜디오 실행 완료!"
echo "============================================"
echo ""
echo "🌐 웹 브라우저에서 다음 주소로 접속하세요:"
echo "   http://localhost:8501"
echo ""
echo "📚 API 문서:"
echo "   http://localhost:8080/docs"
echo ""
echo "프로세스 ID:"
echo "   API Server: $API_PID"
echo "   Web UI: $UI_PID"
echo ""
echo "종료하려면 다음 명령을 실행하세요:"
echo "   kill $API_PID $UI_PID"
echo "============================================"
echo ""

# 프로세스 유지
wait