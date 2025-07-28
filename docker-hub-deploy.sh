#!/bin/bash
# Docker Hub를 통한 이미지 배포

echo "🌐 Docker Hub를 통한 이미지 업로드"
echo "================================="

# Docker Hub 로그인 확인
echo "🔐 Docker Hub 로그인 확인 중..."
if ! docker info | grep -q "Username:"; then
    echo "📝 Docker Hub에 로그인하세요:"
    docker login
fi

# 사용자 입력
read -p "Docker Hub 사용자명을 입력하세요: " DOCKER_USERNAME
read -p "이미지 태그 [latest]: " IMAGE_TAG
IMAGE_TAG=${IMAGE_TAG:-latest}

# 이미지 태그 재지정
FULL_IMAGE_NAME="${DOCKER_USERNAME}/chzzk-auto-recorder:${IMAGE_TAG}"
echo "🏷️  이미지 태그 재지정: ${FULL_IMAGE_NAME}"
docker tag chzzk-auto-recorder:latest ${FULL_IMAGE_NAME}

# Docker Hub에 업로드
echo "📤 Docker Hub에 이미지 업로드 중..."
docker push ${FULL_IMAGE_NAME}

if [ $? -eq 0 ]; then
    echo "✅ 이미지 업로드 성공!"
    echo "🔗 이미지 URL: https://hub.docker.com/r/${DOCKER_USERNAME}/chzzk-auto-recorder"
    
    # NAS 배포용 docker-compose.yml 업데이트
    echo ""
    echo "📋 NAS에서 사용할 docker-compose.yml 설정:"
    echo "---"
    echo "services:"
    echo "  chzzk-recorder:"
    echo "    image: ${FULL_IMAGE_NAME}"
    echo "    # build: .  # 이 라인은 주석 처리"
    echo "    container_name: chzzk-recorder"
    echo "    # ... 나머지 설정은 동일"
    echo "---"
    echo ""
    echo "🚀 NAS에서 실행 방법:"
    echo "1. NAS SSH 접속"
    echo "2. docker-compose.yml에서 image: ${FULL_IMAGE_NAME} 설정"
    echo "3. docker-compose up -d"
    
else
    echo "❌ 이미지 업로드 실패"
    exit 1
fi 