#!/bin/bash

# 치지직 자동 녹화 시스템 - Screen 세션 중지 스크립트
# 사용법: ./stop_recorder.sh

echo "🛑 치지직 자동 녹화 시스템을 중지합니다..."

# 세션 이름 설정
SESSION_NAME="chzzk-recorder"

# 기존 세션이 있는지 확인
if screen -list | grep -q "$SESSION_NAME"; then
    echo "📋 현재 실행 중인 세션:"
    screen -list | grep "$SESSION_NAME"
    echo ""
    echo "⚠️  세션을 종료하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🛑 세션 종료 중..."
        screen -S "$SESSION_NAME" -X quit
        sleep 2
        
        # 종료 확인
        if screen -list | grep -q "$SESSION_NAME"; then
            echo "❌ 세션 종료에 실패했습니다."
        else
            echo "✅ 세션이 성공적으로 종료되었습니다."
        fi
    else
        echo "❌ 종료를 취소합니다."
    fi
else
    echo "❌ 실행 중인 '$SESSION_NAME' 세션이 없습니다."
    echo ""
    echo "🔍 현재 실행 중인 모든 screen 세션:"
    screen -list
fi 