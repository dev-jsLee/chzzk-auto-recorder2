#!/bin/bash

# 치지직 자동 녹화 시스템 - 상태 확인 스크립트
# 사용법: ./status_recorder.sh

echo "🔍 치지직 자동 녹화 시스템 상태 확인..."
echo "========================================"

# 세션 이름 설정
SESSION_NAME="chzzk-recorder"

# 1. Screen 세션 상태 확인
echo "📱 Screen 세션 상태:"
if screen -list | grep -q "$SESSION_NAME"; then
    echo "  ✅ 세션 실행 중: $SESSION_NAME"
    screen -list | grep "$SESSION_NAME"
else
    echo "  ❌ 세션 없음"
fi
echo ""

# 2. 모든 Screen 세션 목록
echo "📋 전체 Screen 세션 목록:"
screen -list
echo ""

# 3. 로그 파일 상태 확인
echo "📄 로그 파일 상태:"
if [ -d "logs" ]; then
    LOG_COUNT=$(ls -1 logs/chzzk_recorder_*.log 2>/dev/null | wc -l)
    if [ "$LOG_COUNT" -gt 0 ]; then
        echo "  📁 로그 디렉토리: logs/"
        echo "  📊 로그 파일 개수: $LOG_COUNT개"
        echo "  📝 최근 로그 파일:"
        ls -t logs/chzzk_recorder_*.log 2>/dev/null | head -3 | while read -r logfile; do
            echo "    - $(basename "$logfile") ($(stat -c %y "$logfile" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1))"
        done
    else
        echo "  📁 로그 디렉토리는 있지만 로그 파일이 없습니다."
    fi
else
    echo "  ❌ logs 디렉토리가 없습니다."
fi
echo ""

# 4. 녹화 파일 상태 확인
echo "🎥 녹화 파일 상태:"
if [ -d "recordings" ]; then
    REC_COUNT=$(ls -1 recordings/*.mp4 2>/dev/null | wc -l)
    if [ "$REC_COUNT" -gt 0 ]; then
        echo "  📁 녹화 디렉토리: recordings/"
        echo "  🎬 녹화 파일 개수: $REC_COUNT개"
        echo "  📝 최근 녹화 파일:"
        ls -t recordings/*.mp4 2>/dev/null | head -3 | while read -r recfile; do
            size=$(du -h "$recfile" 2>/dev/null | cut -f1)
            echo "    - $(basename "$recfile") ($size)"
        done
    else
        echo "  📁 녹화 디렉토리는 있지만 파일이 없습니다."
    fi
else
    echo "  ❌ recordings 디렉토리가 없습니다."
fi
echo ""

# 5. 관리 명령어 안내
echo "🛠️  관리 명령어:"
echo "  - 세션 시작:     ./start_recorder.sh"
echo "  - 세션 중지:     ./stop_recorder.sh"
echo "  - 세션 접속:     screen -r $SESSION_NAME"
echo "  - 세션 분리:     Ctrl+A, D"
echo "  - 로그 실시간:   tail -f logs/chzzk_recorder_YYYYMMDD_HHMMSS.log"
echo "  - 세션 강제종료: screen -S $SESSION_NAME -X quit"
echo ""

# 6. 최근 로그 미리보기 (옵션)
if [ "$1" == "--log" ] || [ "$1" == "-l" ]; then
    echo "📖 최근 로그 미리보기 (마지막 20줄):"
    echo "----------------------------------------"
    LATEST_LOG=$(ls -t logs/chzzk_recorder_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        tail -20 "$LATEST_LOG"
    else
        echo "  ❌ 로그 파일이 없습니다."
    fi
fi 