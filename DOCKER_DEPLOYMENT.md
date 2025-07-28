# 🐳 Docker 배포 가이드 (Synology NAS)

치지직 자동 녹화 시스템을 Synology NAS의 Docker에 배포하는 방법을 설명합니다.

## 📋 사전 준비사항

### 1. Synology NAS 설정
- **DSM 7.2** 이상
- **Docker 패키지** 설치 (패키지 센터에서 설치)
- **SSH 접근** 활성화 (제어판 > 터미널 및 SNMP)

### 2. 필요한 디렉터리 생성
DSM 파일 스테이션에서 다음 폴더들을 생성하세요:

```
/volume1/recordings/chzzk/    # 녹화 파일 저장소
/volume1/logs/chzzk/          # 로그 파일
/volume1/config/chzzk/        # 설정 파일
```

## 🚀 배포 방법

### 방법 1: SSH를 통한 배포 (권장)

#### 1단계: NAS에 SSH 접속
```bash
ssh admin@[NAS_IP_주소]
```

#### 2단계: 프로젝트 디렉터리 생성 및 파일 업로드
```bash
# 작업 디렉터리 생성
mkdir -p /volume1/docker/chzzk-recorder
cd /volume1/docker/chzzk-recorder

# 프로젝트 파일들을 이 위치에 업로드 (SFTP 또는 파일 스테이션 사용)
```

#### 3단계: 환경변수 파일 설정
```bash
# .env 파일 생성
cp env.txt .env
nano .env
```

`.env` 파일 내용:
```env
# 치지직 자동 녹화 시스템 환경변수
NID_AUT=your_nid_aut_cookie_value_here
NID_SES=your_nid_ses_cookie_value_here
CHZZK_CHANNEL_ID=your_target_channel_id_here
DISCORD_WEBHOOK_URL=
```

#### 4단계: Docker 이미지 빌드
```bash
# Docker 이미지 빌드 (시간이 다소 걸릴 수 있음)
docker build -t chzzk-auto-recorder:latest .
```

#### 5단계: 컨테이너 실행
```bash
# docker-compose로 실행
docker-compose up -d

# 또는 직접 docker run
docker run -d \
  --name chzzk-recorder \
  --restart unless-stopped \
  -v /volume1/recordings/chzzk:/app/recordings \
  -v /volume1/logs/chzzk:/app/logs \
  -v /volume1/config/chzzk:/app/config \
  -v /volume1/docker/chzzk-recorder/.env:/app/.env:ro \
  -p 18080:8080 \
  -p 18081:8081 \
  -e TZ=Asia/Seoul \
  chzzk-auto-recorder:latest
```

### 방법 2: DSM Docker GUI 사용

#### 1단계: 이미지 가져오기
1. **제어판 > 작업 스케줄러**에서 사용자 정의 스크립트 생성
2. 스크립트 내용에 빌드 명령어 추가:
```bash
cd /volume1/docker/chzzk-recorder
docker build -t chzzk-auto-recorder:latest .
```

#### 2단계: DSM Docker에서 컨테이너 생성
1. **Docker > 이미지**에서 `chzzk-auto-recorder:latest` 확인
2. **이미지 실행** 클릭
3. 다음 설정 적용:

**볼륨 설정:**
```
/volume1/recordings/chzzk → /app/recordings
/volume1/logs/chzzk → /app/logs  
/volume1/config/chzzk → /app/config
/volume1/docker/chzzk-recorder/.env → /app/.env (읽기 전용)
```

**포트 설정:**
```
로컬 포트 18080 → 컨테이너 포트 8080
로컬 포트 18081 → 컨테이너 포트 8081
```

**환경변수:**
```
TZ=Asia/Seoul
PYTHONUNBUFFERED=1
```

## 📊 컨테이너 상태 확인

### 1. DSM Docker GUI에서 확인
- **Docker > 컨테이너**에서 `chzzk-recorder` 상태 확인
- **로그** 탭에서 실시간 로그 확인
- **터미널** 탭에서 컨테이너 내부 접속

### 2. 컨테이너 내부에서 상태 확인
```bash
# 컨테이너 접속
docker exec -it chzzk-recorder bash

# 상태 확인 스크립트 실행
bash /app/docker/container-status.sh
```

### 3. 헬스체크 확인
```bash
# 헬스체크 실행
docker exec chzzk-recorder python /app/healthcheck.py
```

## 🎯 예상 출력

### 정상 작동 시
```
===========================================
    치지직 자동 녹화 시스템 상태 확인
===========================================
현재 시간: Sun Jul 27 23:30:00 KST 2025

📊 프로세스 상태 (Supervisor):
-------------------------------------------
chzzk-recorder                   RUNNING   pid 123, uptime 0:15:32

🔍 메인 프로세스 확인:
-------------------------------------------  
✅ 메인 녹화 프로세스 실행 중
root     123  0.5  2.1  98765 54321 ?   S    23:15   0:01 python main.py

📝 로그 파일 상태:
-------------------------------------------
로그 디렉터리: /app/logs
-rw-r--r-- 1 root root 15432 Jul 27 23:30 chzzk-recorder.log
-rw-r--r-- 1 root root   256 Jul 27 23:15 supervisord.log

📋 최신 로그 (마지막 10줄):
-------------------------------------------
2025-07-27 23:30:15 - INFO - 방송 상태 확인 중...
2025-07-27 23:30:15 - INFO - 현재 오프라인 상태
2025-07-27 23:30:25 - INFO - 다음 확인까지 10초 대기
```

## 🔧 문제해결

### 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker logs chzzk-recorder

# 환경변수 확인
docker exec chzzk-recorder env | grep CHZZK
```

### 녹화가 시작되지 않는 경우
```bash
# 컨테이너 내부 접속
docker exec -it chzzk-recorder bash

# 직접 테스트
uv run python test_streamlink_recorder.py
```

### 로그 확인
```bash
# 실시간 로그 모니터링
docker exec chzzk-recorder tail -f /app/logs/chzzk-recorder.log

# 오류 로그 확인
docker exec chzzk-recorder tail -f /app/logs/chzzk-recorder-error.log
```

## 🌐 향후 웹 인터페이스

현재는 CLI 기반이지만, 향후 웹 인터페이스가 추가될 예정입니다:

- **상태 모니터링**: `http://[NAS_IP]:18080`
- **설정 관리**: `http://[NAS_IP]:18080/config`
- **녹화 기록**: `http://[NAS_IP]:18080/recordings`

## 📱 DSM 모바일 앱에서 확인

DSM mobile 앱을 통해서도 컨테이너 상태를 확인할 수 있습니다:

1. **Docker** 앱 열기
2. **컨테이너** 탭에서 `chzzk-recorder` 확인
3. **알림 설정**으로 컨테이너 중단 시 알림 받기

## 🔄 업데이트

새 버전 배포 시:

```bash
# 1. 컨테이너 중지
docker-compose down

# 2. 새 코드로 이미지 재빌드  
docker build -t chzzk-auto-recorder:latest .

# 3. 컨테이너 재시작
docker-compose up -d
```

---

**🎉 이제 Synology NAS에서 치지직 방송을 자동으로 녹화할 수 있습니다!** 