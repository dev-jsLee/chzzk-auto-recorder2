# 🚀 빠른 시작 가이드

## 📋 1단계: 환경 설정

### 1.1 FFmpeg 설치 (필수!)

녹화 기능을 위해 FFmpeg가 설치되어 있어야 합니다.

**Windows:**
```bash
# Chocolatey 사용
choco install ffmpeg

# 또는 공식 사이트에서 다운로드
# https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 1.2 uv 설치 및 프로젝트 설정
```bash
# uv로 의존성 설치
uv sync

# 개발 의존성도 함께 설치 (선택사항)
uv sync --extra dev
```

### 1.3 환경변수 설정
```bash
# env.txt를 .env로 복사
cp env.txt .env

# .env 파일 편집
nano .env  # 또는 원하는 편집기 사용
```

**`.env` 파일 설정 방법:**
1. 치지직 웹사이트(https://chzzk.naver.com)에 로그인
2. F12 → Application → Cookies → https://chzzk.naver.com
3. `NID_AUT`와 `NID_SES` 값을 복사해서 `.env`에 입력
4. 모니터링할 채널 ID 입력 (URL에서 확인 가능)

## 🧪 2단계: 테스트 실행

### 2.1 파일명 생성 테스트 (추천!)
```bash
# 파일명 생성 로직 테스트
uv run python filename_test.py
```

**테스트 내용:**
- 카테고리가 있는 경우 파일명 생성
- 카테고리가 없는 경우 파일명 생성 (자동 제외)
- 특수문자 처리 테스트

### 2.2 방송 상태 모니터링 테스트
```bash
# 테스트 스크립트 실행
uv run python test_monitor.py
```

**테스트 메뉴:**
- `1번`: 단일 상태 확인 (현재 방송 상태를 한 번만 확인 + 파일명 생성 테스트)
- `2번`: 연속 모니터링 (3분마다 방송 상태 확인, Ctrl+C로 중지)

### 2.3 녹화 엔진 테스트 ⭐
```bash
# 녹화 엔진 종합 테스트
uv run python test_recorder.py
```

**테스트 내용:**
- ✅ FFmpeg 설치 확인
- ✅ 녹화기 기본 기능 테스트
- ✅ 실제 방송 스트림 녹화 테스트 (10초간)

### 2.4 자동 녹화 시스템 통합 테스트 🚀
```bash
# 자동 녹화 시스템 종합 테스트
uv run python test_auto_recorder.py
```

**테스트 메뉴:**
- `1번`: 설정 검증 테스트
- `2번`: 기본 기능 테스트 (초기화, 콜백 설정 등)
- `3번`: 짧은 실행 테스트 (5분간 자동 녹화)
- `4번`: 연속 모니터링 테스트 (실제 운영 모드)

### 2.5 예상 출력 결과

**방송 중일 때:**
```
🔴 방송 시작 감지!
📺 제목: 오늘도_솔랭_도전
🏷️ 카테고리: 리그_오브_레전드
👤 스트리머: 스트리머_닉네임
👀 시청자 수: 1234명
📁 파일명: 20240115_203015_리그_오브_레전드_오늘도_솔랭_도전.mp4
🎬 자동 녹화 시작!
```

**방송 종료 시:**
```
⏹️ 방송 종료 감지!
🛑 자동 녹화 완료!
📁 파일: 20240115_203015_리그_오브_레전드_오늘도_솔랭_도전.mp4
📊 크기: 125.3MB
⏱️ 시간: 0:45:32
✅ 녹화 파일 생성 확인됨
```

## 🚀 3단계: 실제 자동 녹화 시작

모든 테스트가 통과하면 실제 자동 녹화를 시작할 수 있습니다!

### 3.1 자동 녹화 시스템 실행
```bash
# 실제 자동 녹화 시스템 시작
uv run python main.py
```

**실행 시 나타나는 정보:**
```
============================================================
🚀 치지직 자동 녹화 시스템 시작
============================================================
📺 모니터링 채널: your_channel_id
📁 녹화 저장 경로: ./recordings
🎬 녹화 품질: 1080p
⏰ 폴링 간격: 180초
🔧 FFmpeg 경로: ffmpeg
✅ 설정 검증 완료
============================================================
🔄 시스템 시작 중...
📡 방송 모니터링 시작 (폴링 간격: 180초)
```

### 3.2 시스템 중지
```bash
# Ctrl+C로 안전하게 중지
^C
🛑 사용자에 의해 중단됨
🛑 자동 녹화 시스템 중지 중...
✅ 자동 녹화 시스템 중지 완료
🏁 시스템 종료
```

### 3.3 백그라운드 실행 (NAS/서버 환경)
```bash
# nohup으로 백그라운드 실행
nohup uv run python main.py > chzzk_recorder.log 2>&1 &

# 실행 상태 확인
tail -f chzzk_recorder.log

# 프로세스 종료
pkill -f "python main.py"
```

## ⚠️ 문제 해결

### FFmpeg 관련 오류
```bash
❌ FFmpeg 설치되지 않음: ffmpeg
```
→ FFmpeg를 설치하고 PATH에 추가하세요.

### 환경변수 오류
```bash
❌ 환경변수가 설정되지 않았습니다
```
→ `.env` 파일에 NID_AUT, NID_SES, CHZZK_CHANNEL_ID를 설정하세요.

### HLS URL 없음 오류
```bash
❌ HLS URL이 없습니다
```
→ 방송이 시작되지 않았거나, 쿠키가 만료되었을 수 있습니다.

### 권한 오류 (Linux/macOS)
```bash
❌ Permission denied
```
→ 녹화 저장 경로의 쓰기 권한을 확인하세요.

## 🎯 다음 단계

### 4.1 Docker 컨테이너화 (구현 예정)
```bash
# Docker 이미지 빌드
docker build -t chzzk-auto-recorder .

# 컨테이너 실행
docker run -d --name chzzk-recorder \
  -v /path/to/recordings:/app/recordings \
  -v /path/to/.env:/app/.env \
  chzzk-auto-recorder
```

### 4.2 Synology NAS 배포 (구현 예정)
```bash
# Docker Compose 사용
docker-compose up -d
```

### 🔧 설정 커스터마이징

`config.py`에서 다음 설정들을 변경할 수 있습니다:

- **녹화 경로**: `recording_path`
- **녹화 품질**: `quality` (1080p, 720p, 480p, 360p, 144p)
- **폴링 간격**: `polling_interval` (초 단위)
- **파일명 형식**: `filename_format`

예시:
```python
config.recording.recording_path = Path("/nas/recordings")
config.recording.quality = "720p"
config.recording.polling_interval = 60  # 1분마다 확인
```

## 📊 로그 및 모니터링

### 로그 파일 위치
- **실행 로그**: `./logs/chzzk_recorder.log`
- **테스트 로그**: `test_*.log` 파일들

### 로그 실시간 확인
```bash
# 메인 로그 실시간 확인
tail -f logs/chzzk_recorder.log

# 특정 레벨만 확인
grep "ERROR" logs/chzzk_recorder.log
grep "녹화" logs/chzzk_recorder.log
```

## 🎉 완료!

이제 치지직 방송을 완전 자동으로 녹화하는 시스템이 준비되었습니다! 🚀

- ✅ 방송 시작 자동 감지
- ✅ 자동 녹화 시작
- ✅ 방송 종료 시 자동 중지
- ✅ 파일명 자동 생성
- ✅ 안전한 종료 처리 