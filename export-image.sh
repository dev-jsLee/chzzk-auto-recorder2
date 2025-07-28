#!/bin/bash
# Docker 이미지를 tar 파일로 내보내서 NAS에 전송

echo "🎯 Docker 이미지 내보내기 및 NAS 전송"
echo "======================================"

# 사용자 입력
read -p "NAS IP 주소를 입력하세요: " NAS_IP
read -p "SSH 사용자명 [admin]: " SSH_USER
SSH_USER=${SSH_USER:-admin}

# 1. 로컬 이미지를 tar 파일로 내보내기
echo "📦 Docker 이미지를 tar 파일로 내보내는 중..."
docker save -o chzzk-auto-recorder.tar chzzk-auto-recorder:latest

if [ $? -eq 0 ]; then
    echo "✅ 이미지 내보내기 성공"
    echo "📏 파일 크기: $(du -h chzzk-auto-recorder.tar | cut -f1)"
else
    echo "❌ 이미지 내보내기 실패"
    exit 1
fi

# 2. NAS로 파일 전송
echo "📤 NAS로 파일 전송 중..."
scp chzzk-auto-recorder.tar ${SSH_USER}@${NAS_IP}:/volume1/docker/

if [ $? -eq 0 ]; then
    echo "✅ 파일 전송 성공"
else
    echo "❌ 파일 전송 실패"
    exit 1
fi

# 3. NAS에서 이미지 로드
echo "🐳 NAS에서 Docker 이미지 로드 중..."
ssh ${SSH_USER}@${NAS_IP} << 'EOF'
cd /volume1/docker
sudo docker load -i chzzk-auto-recorder.tar

if [ $? -eq 0 ]; then
    echo "✅ 이미지 로드 성공"
    echo "📋 이미지 확인:"
    sudo docker images | grep chzzk-auto-recorder
    
    # tar 파일 정리
    rm -f chzzk-auto-recorder.tar
    echo "🧹 임시 파일 정리 완료"
else
    echo "❌ 이미지 로드 실패"
    exit 1
fi
EOF

# 4. 로컬 tar 파일 정리
rm -f chzzk-auto-recorder.tar

echo ""
echo "🎉 이미지 전송 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 프로젝트 파일도 전송해야 합니다:"
echo "   ./nas-deploy.sh  # 또는 수동으로 docker-compose.yml, .env 등 전송"
echo ""
echo "2. NAS에서 컨테이너 실행:"
echo "   ssh ${SSH_USER}@${NAS_IP}"
echo "   cd /volume1/docker/chzzk-recorder"
echo "   sudo docker-compose up -d" 