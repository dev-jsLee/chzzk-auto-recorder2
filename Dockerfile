# 치지직 자동 녹화 시스템 Docker 이미지
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="py311-chzzk-auto-recorder"
LABEL description="치지직 방송 자동 녹화 시스템"
LABEL version="1.0.0"

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Seoul

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    # 기본 도구들
    curl \
    wget \
    ca-certificates \
    gnupg \
    # FFmpeg 및 미디어 처리
    ffmpeg \
    # 네트워크 도구
    iputils-ping \
    telnet \
    # 로그 관리
    logrotate \
    # 시간대 설정
    tzdata \
    # 프로세스 관리
    supervisor \
    # 정리
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (빠른 Python 패키지 관리)
RUN pip install --no-cache-dir uv

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY main.py ./

# 의존성 설치
RUN uv sync --frozen

# 디렉터리 생성
RUN mkdir -p /app/recordings /app/logs /app/config

# supervisor 설정 파일 생성
RUN mkdir -p /var/log/supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 로그 설정
COPY docker/logrotate.conf /etc/logrotate.d/chzzk-recorder

# 헬스체크 스크립트
COPY docker/healthcheck.py /app/healthcheck.py

# 웹 관리 인터페이스용 디렉터리 (향후 사용)
RUN mkdir -p /app/web

# 권한 설정
RUN chmod +x /app/healthcheck.py

# 포트 노출
# 8080: 웹 관리 인터페이스 (향후)
# 8081: 상태 모니터링 API (향후)
EXPOSE 8080 8081

# 볼륨 마운트 포인트
VOLUME ["/app/recordings", "/app/logs", "/app/config"]

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/healthcheck.py

# supervisor로 프로세스 관리
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 