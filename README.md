# Naver News AI Summarizer

네이버 뉴스 API와 OpenAI를 활용한 뉴스 검색 및 자동 그룹화/요약 서비스

## 주요 기능

- 🔍 **키워드 기반 뉴스 검색**: Naver Open API를 통한 실시간 뉴스 검색
- 🤖 **AI 기반 그룹화**: OpenAI Embeddings를 사용한 유사 뉴스 자동 그룹화
- 📊 **종목별 그룹화**: 시가총액 상위 종목 기준 뉴스 분류
- 💰 **실시간 주가 정보**: 종목별 현재가 및 등락률 표시
- 📝 **AI 요약**: GPT를 활용한 뉴스 그룹 자동 요약
- 📅 **날짜 필터링**: 원하는 기간의 뉴스만 조회
- ⚙️ **설정 저장**: 사용자 설정 자동 저장 및 복원

## 기술 스택

- **Frontend**: Streamlit
- **APIs**: 
  - Naver Open API (뉴스 검색)
  - OpenAI API (임베딩, 요약)
  - FinanceDataReader (주식 데이터)
- **Language**: Python 3.9+

## 설치 방법

### 1. 저장소 클론

```bash
git clone <your-repo-url>
cd infinite-apogee
```

### 2. 가상환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 API 키를 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
OPENAI_API_KEY=your_openai_api_key
```

### 5. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

## API 키 발급

### Naver Open API
1. [Naver Developers](https://developers.naver.com/) 접속
2. 애플리케이션 등록
3. 검색 > 뉴스 API 선택
4. Client ID와 Client Secret 발급

### OpenAI API
1. [OpenAI Platform](https://platform.openai.com/) 접속
2. API Keys 메뉴에서 새 키 생성
3. 발급된 키 복사

## 사용 방법

1. **검색 키워드 입력**: 관심 있는 주제나 종목명 입력
2. **그룹화 방법 선택**:
   - **Semantic Similarity (AI)**: 의미적 유사도 기반 그룹화
   - **Stock Name Matching**: 종목명 기반 그룹화
3. **날짜 범위 설정**: 검색할 뉴스의 기간 선택
4. **검색 실행**: 결과 확인 및 AI 요약 확인

## 배포

자세한 배포 방법은 [DEPLOYMENT.md](DEPLOYMENT.md)를 참고하세요.

- Streamlit Community Cloud (무료, 추천)
- Docker
- AWS/GCP/Azure

## 프로젝트 구조

```
.
├── app.py                 # 메인 Streamlit 앱
├── news_logic.py          # 뉴스 검색 및 그룹화 로직
├── stock_logic.py         # 주식 데이터 처리
├── config_logic.py        # 설정 관리
├── requirements.txt       # Python 패키지 목록
├── .env.example          # 환경 변수 예시
├── DEPLOYMENT.md         # 배포 가이드
└── .streamlit/
    └── config.toml       # Streamlit 설정
```

## 라이선스

MIT License

## 기여

이슈 및 PR은 언제나 환영합니다!
