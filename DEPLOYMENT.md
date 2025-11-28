# Naver News AI Summarizer - Deployment Guide

## Option 1: Streamlit Community Cloud (추천)

가장 간단하고 무료로 배포할 수 있는 방법입니다.

### 사전 준비

1. **GitHub 저장소 생성**
   ```bash
   cd /Users/hongjong/.gemini/antigravity/playground/infinite-apogee
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **GitHub에 푸시**
   - GitHub에서 새 저장소 생성
   - 로컬 저장소를 GitHub에 연결하고 푸시

### 배포 단계

1. **Streamlit Community Cloud 접속**
   - https://streamlit.io/cloud 방문
   - GitHub 계정으로 로그인

2. **New app 클릭**
   - Repository: 방금 생성한 저장소 선택
   - Branch: `main`
   - Main file path: `app.py`

3. **Secrets 설정**
   - Advanced settings → Secrets 클릭
   - 아래 내용을 입력:
   ```toml
   NAVER_CLIENT_ID = "your_naver_client_id"
   NAVER_CLIENT_SECRET = "your_naver_client_secret"
   OPENAI_API_KEY = "your_openai_api_key"
   ```

4. **Deploy 클릭**
   - 몇 분 후 앱이 배포됩니다
   - 공개 URL이 생성됩니다 (예: `https://your-app.streamlit.app`)

## Option 2: Docker 배포

### Dockerfile 생성

프로젝트에 `Dockerfile`이 이미 포함되어 있습니다.

### 빌드 및 실행

```bash
# Docker 이미지 빌드
docker build -t naver-news-app .

# 컨테이너 실행
docker run -p 8501:8501 \
  -e NAVER_CLIENT_ID="your_id" \
  -e NAVER_CLIENT_SECRET="your_secret" \
  -e OPENAI_API_KEY="your_key" \
  naver-news-app
```

### Docker Compose 사용

```bash
# .env 파일 설정 후
docker-compose up -d
```

## Option 3: AWS/GCP/Azure

### AWS EC2 예시

1. **EC2 인스턴스 생성** (Ubuntu 22.04 추천)

2. **SSH 접속 후 설정**
   ```bash
   # Python 및 필요 패키지 설치
   sudo apt update
   sudo apt install python3-pip python3-venv -y
   
   # 프로젝트 클론
   git clone <your-repo-url>
   cd infinite-apogee
   
   # 가상환경 생성 및 활성화
   python3 -m venv .venv
   source .venv/bin/activate
   
   # 패키지 설치
   pip install -r requirements.txt
   
   # .env 파일 생성
   nano .env
   # (API 키 입력)
   
   # 앱 실행
   streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   ```

3. **백그라운드 실행 (systemd)**
   - `/etc/systemd/system/streamlit-app.service` 파일 생성
   - 서비스 등록 및 시작

4. **보안 그룹 설정**
   - 포트 8501 인바운드 규칙 추가

## 주의사항

### API 키 보안
- `.env` 파일은 절대 GitHub에 푸시하지 마세요
- `.gitignore`에 `.env`가 포함되어 있는지 확인하세요
- Streamlit Cloud의 Secrets 기능을 사용하세요

### 성능 최적화
- 주식 데이터 캐싱: `@st.cache_data` 데코레이터 추가 고려
- API 호출 제한: Rate limiting 구현 고려

### 비용 관리
- OpenAI API 사용량 모니터링
- Naver API 일일 호출 제한 확인

## 추천 배포 방법

**개인/테스트용**: Streamlit Community Cloud (무료)  
**프로덕션**: AWS/GCP + Docker (확장성, 제어 가능)
