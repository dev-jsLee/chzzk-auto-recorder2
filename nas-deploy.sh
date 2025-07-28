#!/bin/bash
# Synology NAS 직접 배포 스크립트

echo "🚀 치지직 자동 녹화 시스템 - NAS 배포"
echo "====================================="

# 사용자 입력 받기
read -p "NAS IP 주소를 입력하세요: " NAS_IP
read -p "SSH 사용자명 [admin]: " SSH_USER
SSH_USER=${SSH_USER:-admin}

echo "📁 NAS에 디렉터리 생성 중..."

# NAS에 디렉터리 생성
ssh ${SSH_USER}@${NAS_IP} << 'EOF'
# 작업 디렉터리 생성
sudo mkdir -p /volume1/docker/chzzk-recorder
sudo mkdir -p /volume1/recordings/chzzk
sudo mkdir -p /volume1/logs/chzzk  
sudo mkdir -p /volume1/config/chzzk

# 권한 설정
sudo chown -R ${USER}:users /volume1/docker/chzzk-recorder
sudo chown -R ${USER}:users /volume1/recordings/chzzk
sudo chown -R ${USER}:users /volume1/logs/chzzk
sudo chown -R ${USER}:users /volume1/config/chzzk

echo "✅ 디렉터리 생성 완료"
EOF

echo "📤 프로젝트 파일 업로드 중..."

# 필요한 파일들만 압축
tar -czf chzzk-recorder.tar.gz \
    --exclude='*.log' \
    --exclude='test_recordings' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    Dockerfile docker-compose.yml \
    pyproject.toml uv.lock \
    src/ main.py docker/ \
    env.txt DOCKER_DEPLOYMENT.md

# NAS로 파일 전송
scp chzzk-recorder.tar.gz ${SSH_USER}@${NAS_IP}:/volume1/docker/chzzk-recorder/

echo "🔧 NAS에서 설정 및 빌드 중..."

# NAS에서 압축 해제 및 빌드
ssh ${SSH_USER}@${NAS_IP} << 'EOF'
cd /volume1/docker/chzzk-recorder

# 압축 해제
tar -xzf chzzk-recorder.tar.gz
rm chzzk-recorder.tar.gz

# 환경변수 파일 설정
if [ ! -f .env ]; then
    cp env.txt .env
    echo "⚠️  .env 파일을 편집하여 실제 값을 입력하세요:"
    echo "   nano .env"
else
    echo "✅ .env 파일이 이미 존재합니다"
fi

# Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 중... (시간이 걸릴 수 있습니다)"
sudo docker build -t chzzk-auto-recorder:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 성공!"
    echo "📋 이미지 확인:"
    sudo docker images | grep chzzk-auto-recorder
else
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi
EOF

# 로컬 임시 파일 정리
rm -f chzzk-recorder.tar.gz

echo ""
echo "🎉 배포 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. NAS에 SSH 접속: ssh ${SSH_USER}@${NAS_IP}"
echo "2. 설정 디렉터리로 이동: cd /volume1/docker/chzzk-recorder"
echo "3. 환경변수 편집: nano .env"
echo "4. 컨테이너 실행: sudo docker-compose up -d"
echo ""
echo "🔍 상태 확인: sudo docker logs chzzk-recorder" 