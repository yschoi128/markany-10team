# AI 식단 코치 (AI Diet Coach)

AWS 기반의 개인 맞춤형 식단 관리 AI 솔루션입니다.

## 🚀 주요 기능

- **식사 이미지 분석**: 사진 촬영 시 음식 종류, 칼로리, 영양소 자동 분석
- **AI PT 코칭**: 개인 목표 기반 맞춤형 식단/운동 처방 및 실시간 조언
- **스케줄 연동 관리**: 회식 등 예정된 식사 스케줄링 및 사전/사후 관리
- **대화형 인터페이스**: 음성/텍스트 기반 자연어 대화
- **개인화 추천**: 사용자 프로필 기반 맞춤형 식단 및 운동 추천

## 🏗️ 아키텍처

```
├── src/
│   ├── config/          # AWS 설정 및 환경 변수 관리
│   ├── models/          # 데이터 모델 정의 (Pydantic)
│   ├── services/        # AWS 서비스별 모듈
│   │   ├── s3_service.py
│   │   ├── bedrock_service.py
│   │   └── dynamodb_service.py
│   ├── pipelines/       # 비즈니스 로직 파이프라인
│   │   ├── food_analysis_pipeline.py
│   │   └── coaching_pipeline.py
│   ├── utils/           # 공통 유틸리티
│   └── main.py          # FastAPI 메인 애플리케이션
├── tests/               # 테스트 코드
├── requirements.txt     # 의존성 패키지
└── .env.example        # 환경 변수 템플릿
```

## 🛠️ 설치 및 설정

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 AWS 자격 증명을 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일에서 다음 값들을 설정:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- S3_BUCKET_NAME
- DYNAMODB_DIET_TABLE
- BEDROCK_MODEL_ID

### 3. AWS 리소스 생성

필요한 AWS 리소스들을 생성하세요:

#### S3 버킷
```bash
aws s3 mb s3://ai-diet-coach-images
aws s3 mb s3://ai-diet-coach-profiles
```

#### DynamoDB 테이블
```bash
# 사용자 프로필 테이블
aws dynamodb create-table \
    --table-name user_profiles \
    --attribute-definitions AttributeName=user_id,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# 식사 기록 테이블
aws dynamodb create-table \
    --table-name diet_records \
    --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=meal_id,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH AttributeName=meal_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

# 스케줄 테이블
aws dynamodb create-table \
    --table-name schedule_records \
    --attribute-definitions AttributeName=event_id,AttributeType=S \
    --key-schema AttributeName=event_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

## 🚀 실행

### 개발 서버 실행
```bash
python run.py
```

또는

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 시작되면 다음 URL에서 접근 가능합니다:
- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API 사용법

### 1. 사용자 프로필 생성
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "name": "홍길동",
    "age": 30,
    "gender": "male",
    "height": 175,
    "weight": 70,
    "health_goal": "weight_loss",
    "preferred_exercises": ["gym", "running"],
    "activity_level": "moderate"
  }'
```

### 2. 식사 이미지 분석
```bash
curl -X POST "http://localhost:8000/meals/analyze" \
  -F "user_id=user123" \
  -F "meal_type=점심" \
  -F "people_count=1" \
  -F "image=@meal_photo.jpg"
```

### 3. 일일 코칭 메시지 생성
```bash
curl -X POST "http://localhost:8000/coaching/daily/user123"
```

### 4. AI 코치와 대화
```bash
curl -X POST "http://localhost:8000/coaching/chat/user123" \
  -F "message=오늘 치킨 먹어도 될까요?"
```

## 🧪 테스트

```bash
# 단위 테스트 실행
python -m pytest tests/

# 커버리지 포함 테스트
python -m pytest tests/ --cov=src
```

## 📊 모니터링

애플리케이션은 다음과 같은 모니터링 기능을 제공합니다:

- **로깅**: 구조화된 로그 출력 (`logs/app.log`)
- **헬스체크**: `/health` 엔드포인트
- **메트릭**: CloudWatch 연동 (선택사항)

## 🔧 개발 가이드

### 코드 구조

1. **모델 정의** (`src/models/`): Pydantic 모델로 타입 안전성 보장
2. **서비스 레이어** (`src/services/`): AWS 서비스별 추상화
3. **파이프라인** (`src/pipelines/`): 비즈니스 로직 구현
4. **API 레이어** (`src/main.py`): FastAPI 엔드포인트

### 새로운 기능 추가

1. 데이터 모델을 `src/models/data_models.py`에 정의
2. 필요한 서비스 로직을 `src/services/`에 구현
3. 비즈니스 로직을 `src/pipelines/`에 파이프라인으로 구현
4. API 엔드포인트를 `src/main.py`에 추가

### 코딩 스타일

- **타입 힌트**: 모든 함수에 타입 힌트 사용
- **문서화**: docstring으로 함수 설명
- **에러 처리**: 적절한 예외 처리 및 로깅
- **비동기**: I/O 작업은 async/await 사용

## 🚀 배포

### Docker 배포
```bash
# Dockerfile 생성 후
docker build -t ai-diet-coach .
docker run -p 8000:8000 ai-diet-coach
```

### AWS Lambda 배포
```bash
# Mangum을 사용한 Lambda 배포
pip install mangum
# lambda_handler.py 생성 후 배포
```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

**AI 식단 코치**로 건강한 라이프스타일을 시작하세요! 🥗💪