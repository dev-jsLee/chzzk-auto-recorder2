# 윈도우 PowerShell용 Docker Hub 업로드 스크립트

Write-Host "🌐 Docker Hub 이미지 업로드 (Windows)" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Docker Hub 사용자명 입력
$dockerUsername = Read-Host "Docker Hub 사용자명을 입력하세요"
$imageTag = Read-Host "이미지 태그를 입력하세요 (기본값: latest)"

if ([string]::IsNullOrEmpty($imageTag)) {
    $imageTag = "latest"
}

$fullImageName = "$dockerUsername/chzzk-auto-recorder:$imageTag"

Write-Host ""
Write-Host "📋 업로드 정보:" -ForegroundColor Yellow
Write-Host "로컬 이미지: chzzk-auto-recorder:latest" -ForegroundColor White
Write-Host "업로드 이미지: $fullImageName" -ForegroundColor White
Write-Host ""

# 1. 현재 이미지 확인
Write-Host "🔍 현재 로컬 이미지 확인 중..." -ForegroundColor Blue
docker images | findstr chzzk-auto-recorder

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 로컬에 chzzk-auto-recorder:latest 이미지가 없습니다!" -ForegroundColor Red
    Write-Host "먼저 다음 명령어로 이미지를 빌드하세요:" -ForegroundColor Yellow
    Write-Host "docker build -t chzzk-auto-recorder:latest ." -ForegroundColor White
    exit 1
}

# 2. 이미지 태그 재설정
Write-Host ""
Write-Host "🏷️ 이미지 태그 재설정 중..." -ForegroundColor Blue
docker tag chzzk-auto-recorder:latest $fullImageName

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 태그 재설정 성공" -ForegroundColor Green
} else {
    Write-Host "❌ 태그 재설정 실패" -ForegroundColor Red
    exit 1
}

# 3. Docker Hub 로그인 상태 확인
Write-Host ""
Write-Host "🔐 Docker Hub 로그인 상태 확인 중..." -ForegroundColor Blue
$dockerInfo = docker info 2>$null
if ($dockerInfo -match "Username") {
    Write-Host "✅ Docker Hub에 로그인되어 있습니다" -ForegroundColor Green
} else {
    Write-Host "⚠️ Docker Hub 로그인 상태를 확인할 수 없습니다" -ForegroundColor Yellow
    Write-Host "필요시 다음 명령어로 로그인하세요: docker login" -ForegroundColor White
}

# 4. Docker Hub에 업로드
Write-Host ""
Write-Host "📤 Docker Hub에 이미지 업로드 중..." -ForegroundColor Blue
Write-Host "이 과정은 시간이 걸릴 수 있습니다..." -ForegroundColor Yellow

docker push $fullImageName

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 이미지 업로드 성공!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 업로드 완료 정보:" -ForegroundColor Yellow
    Write-Host "이미지 URL: https://hub.docker.com/r/$dockerUsername/chzzk-auto-recorder" -ForegroundColor White
    Write-Host "Pull 명령어: docker pull $fullImageName" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 Synology NAS에서 사용하는 방법:" -ForegroundColor Yellow
    Write-Host "1. docker-compose.yml에서 다음과 같이 수정:" -ForegroundColor White
    Write-Host "   image: $fullImageName" -ForegroundColor Cyan
    Write-Host "   # build: .  <- 이 줄은 주석 처리" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. NAS에서 실행:" -ForegroundColor White
    Write-Host "   docker-compose up -d" -ForegroundColor Cyan
    
} else {
    Write-Host ""
    Write-Host "❌ 이미지 업로드 실패" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 문제해결 방법:" -ForegroundColor Yellow
    Write-Host "1. Docker Hub 로그인 확인: docker login" -ForegroundColor White
    Write-Host "2. 네트워크 연결 확인" -ForegroundColor White
    Write-Host "3. 이미지 크기가 클 경우 시간을 두고 재시도" -ForegroundColor White
    exit 1
}

# 5. 로컬 태그된 이미지 정리 (선택사항)
Write-Host ""
$cleanup = Read-Host "로컬에서 태그된 이미지를 삭제하시겠습니까? (y/N)"
if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    Write-Host "🧹 로컬 태그 이미지 정리 중..." -ForegroundColor Blue
    docker rmi $fullImageName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 로컬 태그 이미지 삭제 완료" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✨ 모든 작업이 완료되었습니다!" -ForegroundColor Green 