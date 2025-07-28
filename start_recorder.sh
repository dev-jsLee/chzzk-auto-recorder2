#!/bin/bash

# 치지직 자동 녹화 시스템 - Screen 백그라운드 실행 스크립트
# 사용법: ./start_recorder.sh

echo "🎬 치지직 자동 녹화 시스템을 시작합니다..."

# 현재 스크립트 위치로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 환경변수 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다. env.txt를 참고하여 .env 파일을 생성해주세요."
    exit 1
fi

# 세션 이름 설정
SESSION_NAME="chzzk-recorder"

# 기존 세션이 있는지 확인
if screen -list | grep -q "$SESSION_NAME"; then
    echo "⚠️  기존 세션이 실행 중입니다. 종료 후 다시 시작하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🛑 기존 세션 종료 중..."
        screen -S "$SESSION_NAME" -X quit
        sleep 2
    else
        echo "❌ 실행을 취소합니다."
        exit 1
    fi
fi

# 로그 디렉토리 생성
mkdir -p logs

# 현재 시간을 로그 파일명에 포함
LOG_FILE="logs/chzzk_recorder_$(date +%Y%m%d_%H%M%S).log"

echo "📂 로그 파일: $LOG_FILE"
echo "🔄 Screen 세션 '$SESSION_NAME' 시작 중..."

# Screen 세션에서 main.py 실행
screen -dmS "$SESSION_NAME" bash -c "
    echo '🚀 치지직 자동 녹화 시스템 시작...' | tee -a '$LOG_FILE'
    echo '📅 시작 시간: $(date)' | tee -a '$LOG_FILE'
    echo '📁 작업 디렉토리: $(pwd)' | tee -a '$LOG_FILE'
    echo '========================================' | tee -a '$LOG_FILE'
    
    # Python 환경 및 main.py 실행
    uv run python main.py 2>&1 | tee -a '$LOG_FILE'
    
    echo '========================================' | tee -a '$LOG_FILE'
    echo '⏹️ 프로그램 종료: $(date)' | tee -a '$LOG_FILE'
    
    # 종료 후 10초 대기 (로그 확인용)
    echo '10초 후 세션이 종료됩니다...'
    sleep 10
"

# 잠시 대기 후 상태 확인
sleep 2

# 세션 상태 확인
if screen -list | grep -q "$SESSION_NAME"; then
    echo "✅ Screen 세션이 성공적으로 시작되었습니다!"
    echo ""
    echo "📋 관리 명령어:"
    echo "  - 세션 접속:     screen -r $SESSION_NAME"
    echo "  - 세션 분리:     Ctrl+A, D"
    echo "  - 세션 종료:     screen -S $SESSION_NAME -X quit"
    echo "  - 세션 목록:     screen -list"
    echo "  - 로그 실시간:   tail -f $LOG_FILE"
    echo ""
    echo "🔍 현재 실행 중인 세션:"
    screen -list
else
    echo "❌ Screen 세션 시작에 실패했습니다."
    echo "💡 다음을 확인해주세요:"
    echo "  1. screen 패키지가 설치되어 있는지"
    echo "  2. .env 파일이 올바르게 설정되어 있는지"
    echo "  3. uv 환경이 제대로 설정되어 있는지"
    exit 1
fi 