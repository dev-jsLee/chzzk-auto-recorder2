# 치지직 자동 녹화 시스템 (Chzzk Auto Recorder)

> 치지직(Chzzk) 방송 플랫폼의 방송 상태를 감지하여 자동으로 녹화하는 시스템

## 📋 프로젝트 개요

치지직 방송 플랫폼에서 특정 스트리머의 방송 시작/종료를 실시간으로 감지하고, 방송이 시작되면 자동으로 영상을 녹화하여 저장하는 자동화 시스템입니다.

## 🎯 주요 기능

### 1차 목표 (MVP) ✅ **완료!**
- [x] 치지직 방송 상태 실시간 모니터링
- [x] 방송 시작/종료 자동 감지
- [x] 방송 시작 시 자동 녹화 시작
- [x] 방송 종료 시 자동 녹화 중단 및 파일 저장
- [x] 녹화 파일 자동 관리 (파일명, 저장 위치)

### 향후 확장 기능
- [ ] 다중 스트리머 동시 모니터링
- [ ] 녹화 품질 설정 (해상도, 비트레이트)
- [ ] 웹 대시보드 (녹화 상태 모니터링)
- [ ] 디스코드/텔레그램 알림 연동
- [ ] 자동 업로드 (유튜브, 클라우드 스토리지)
- [ ] 녹화 파일 자동 압축 및 정리

## 🏗️ 기술 스택

### 개발 환경
- **언어**: Python 3.11+
- **패키지 관리**: uv
- **컨테이너**: Docker
- **배포 환경**: Synology DSM 7.2

### 주요 라이브러리 (예정)
- **HTTP 클라이언트**: httpx, aiohttp
- **비디오 처리**: ffmpeg-python
- **스케줄링**: APScheduler
- **설정 관리**: pydantic-settings
- **로깅**: structlog
- **웹 프레임워크**: FastAPI (대시보드용)

## 🚀 시스템 요구사항

### 최소 요구사항
- **Python**: 3.11 이상
- **메모리**: 1GB RAM 이상
- **저장공간**: 녹화 파일 저장용 충분한 디스크 공간
- **네트워크**: 안정적인 인터넷 연결

### 권장 요구사항
- **메모리**: 2GB RAM 이상
- **CPU**: 멀티코어 프로세서 (동시 녹화 시)
- **저장공간**: SSD 권장 (I/O 성능)

## 📁 프로젝트 구조

```
py311-chzzk-auto-recorder/
├── src/
│   ├── chzzk_recorder/
│   │   ├── __init__.py
│   │   ├── api/          # 치지직 API 클라이언트
│   │   ├── recorder/     # 녹화 엔진
│   │   ├── monitor/      # 방송 상태 모니터링
│   │   ├── storage/      # 파일 저장 관리
│   │   └── config/       # 설정 관리
│   └── main.py
├── tests/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   └── settings.yaml
├── pyproject.toml
├── uv.lock
└── README.md
```

## 🔧 개발환경 설정

### 1. uv 설치 및 프로젝트 초기화
```bash
# uv 설치 (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 프로젝트 의존성 설치
uv sync

# 개발 모드로 실행
uv run python src/main.py
```

### 2. Docker 개발환경
```bash
# 개발용 컨테이너 빌드
docker build -f docker/Dockerfile -t chzzk-recorder:dev .

# 개발 서버 실행
docker-compose -f docker/docker-compose.dev.yml up
```

## 🚀 사용법

### 기본 사용법
```bash
# 1. 환경변수 설정
cp env.txt .env
# .env 파일 편집 (쿠키 값 입력)

# 2. 자동 녹화 시스템 시작
uv run python main.py
```

### 테스트 실행
```bash
# 개별 모듈 테스트
uv run python test_monitor.py     # 방송 모니터링 테스트
uv run python test_recorder.py    # 녹화 엔진 테스트
uv run python filename_test.py    # 파일명 생성 테스트

# 통합 시스템 테스트
uv run python test_auto_recorder.py
```

### 백그라운드 실행
```bash
# nohup으로 백그라운드 실행
nohup uv run python main.py > chzzk_recorder.log 2>&1 &

# 실행 상태 확인
tail -f chzzk_recorder.log
```

## 🐳 Docker 배포 (구현 예정)

### Synology NAS 배포
```bash
# 프로덕션 이미지 빌드
docker build -t chzzk-recorder:latest .

# Docker Compose로 배포
docker-compose up -d
```

### 환경 변수 설정
```env
# .env 파일
CHZZK_CHANNEL_ID=your_channel_id
NID_AUT=your_nid_aut_cookie
NID_SES=your_nid_ses_cookie
```

## 📊 모니터링 및 로깅

- **로그 레벨**: DEBUG, INFO, WARNING, ERROR
- **로그 포맷**: JSON 구조화 로그
- **모니터링**: 방송 상태, 녹화 상태, 시스템 리소스
- **알림**: 녹화 시작/종료, 에러 상황

## 🛠️ 개발 로드맵

### Phase 1: 핵심 기능 구현 ✅ **완료!**
- ✅ Week 1: 치지직 API 연동 및 방송 상태 감지
- ✅ Week 2: 녹화 엔진 구현 (ffmpeg 연동)
- ✅ Week 3: 자동 녹화 시스템 통합 및 파일 관리
- ✅ Week 4: 통합 테스트 및 버그 수정

### Phase 2: 안정화 및 배포 🔄 **진행 중**
- [ ] Week 5: Docker 컨테이너화 및 최적화
- [ ] Week 6: Synology NAS 배포 테스트

### Phase 3: 확장 기능 (향후)
- [ ] 웹 대시보드 개발
- [ ] 다중 채널 지원
- [ ] 알림 시스템 구축

## 📝 기여 가이드

1. Fork this repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 지원

- **이슈 리포트**: GitHub Issues
- **기능 요청**: GitHub Discussions
- **개발 문의**: 프로젝트 메인테이너에게 연락

---

> **주의사항**: 이 프로젝트는 개인적인 학습 및 연구 목적으로 개발되었습니다. 
> 치지직 플랫폼의 서비스 약관을 준수하여 사용하시기 바랍니다.
