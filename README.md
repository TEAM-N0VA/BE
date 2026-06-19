# mealdang-backend

Meal당 프로젝트의 백엔드 서버 리포지토리입니다. 이 서버는 사용자 인증, 식단 기록, 혈당 데이터 관리, 식후 혈당 예측 요청, 맞춤형 식단·식당 추천, 챗봇 요청 처리 등 Meal당 서비스의 핵심 비즈니스 로직을 담당합니다. Django, Django REST Framework, PostgreSQL, Celery, RabbitMQ, JWT, FastAPI AI 서버, YOLOv8, LightGBM, RAG 등의 기술을 기반으로 구현되어 있습니다.

## ✨ 프로젝트 개요

**Meal당**은 지속적인 혈당 관리가 필요한 임신성 당뇨 산모를 위한 AI 기반 식단·혈당 관리 서비스입니다. 사용자가 매번 식단을 직접 검색하고 입력해야 하는 부담을 줄이고, 식사 전후의 혈당 불안을 완화할 수 있도록 다음과 같은 기능을 제공합니다.

- 🍱 **YOLOv8 기반 식단 자동 기록**  
  음식 사진을 분석하여 음식 종류를 탐지하고, 영양성분 DB와 매핑해 식단 기록을 자동화합니다.

- 📈 **LightGBM 기반 식후 혈당 예측**  
  식단 정보, 영양성분, 식전 혈당, 과거 혈당 기록을 바탕으로 식후 2시간 예상 혈당을 예측합니다.

- 🥗 **맞춤형 식단 추천**  
  임신 주수, 목표 영양성분, 식이 제한, 과거 혈당 반응 등을 반영해 개인화된 식단을 추천합니다.

- 📍 **위치 기반 식당 추천**  
  카카오맵 API로 주변 식당을 조회하고, 영양성분 정보와 사용자 혈당 반응 이력을 기반으로 식당별 안전 점수를 제공합니다.

- 💬 **RAG 기반 식단 코칭 챗봇**  
  임신성 당뇨 FAQ와 가이드라인을 기반으로 사용자 질문에 대해 근거 있는 식단·혈당 관리 답변을 제공합니다.

Meal당 Backend는 위 기능을 실현하기 위해 다음 역할을 수행합니다.

- 사용자 인증 및 JWT 기반 보안 처리
- 사용자 프로필, 임신 정보, 식이 제한, 목표 영양성분 관리
- 식단 기록, 음식 항목, 영양성분 데이터 저장
- 혈당 실측값 및 예측값 저장
- FastAPI 기반 AI 서버와 통신하여 음식 인식, 혈당 예측, 챗봇 응답 결과 처리
- 카카오맵 API 및 식약처 영양성분 데이터 연동
- PostgreSQL 기반 데이터 저장 및 조회
- Celery, RabbitMQ 기반 비동기 작업 처리

---

## 사전 설치 / 필요 항목

### Python

Python 3.11 이상을 권장합니다.

설치 확인:

```bash
python --version
```

또는:

```bash
python3 --version
```

### PostgreSQL

Meal당 Backend는 PostgreSQL을 데이터베이스로 사용합니다.

macOS:

```bash
brew install postgresql
brew services start postgresql
```

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
```

Windows:

PostgreSQL 공식 설치 파일을 통해 설치합니다.


### 외부 API 키

다음 기능을 사용하려면 외부 API 키가 필요합니다.

- 카카오맵 API
- 식약처 영양성분 API
- Gemini API 또는 기타 LLM API
- FastAPI AI 서버 주소

민감한 값은 README에 직접 작성하지 않습니다. 프로젝트에 포함된 `.env.example`, `.env.sample`, `settings.py`, 또는 팀 내부 환경변수 문서를 확인해 `.env` 파일을 작성하세요.

---

## 설치 및 실행 방법

### 1. 레포지토리 클론

```bash
git clone <백엔드_레포지토리_URL>
cd mealdang-backend
```

예시:

```bash
git clone https://github.com/<organization>/mealdang-backend.git
cd mealdang-backend
```

Django 프로젝트가 하위 폴더에 있는 경우 해당 폴더로 이동합니다.

```bash
cd <django_project_folder>
```

### 2. 가상환경 생성 및 활성화

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

AI 서버가 별도 폴더 또는 별도 레포지토리로 분리되어 있다면, AI 서버 폴더에서도 별도로 의존성을 설치해야 합니다.

```bash
cd <ai_server_folder>
pip install -r requirements.txt
```

### 4. 환경 변수 설정

프로젝트에 포함된 예시 환경 파일을 확인합니다.

```bash
ls -a
```

`.env.example`  복사해서 사용합니다.


### 5. 데이터베이스 생성

PostgreSQL에 접속합니다.

```bash
psql postgres
```

또는 Ubuntu 환경에서:

```bash
sudo -u postgres psql
```

데이터베이스와 사용자를 생성합니다. 실제 DB 이름, 사용자명, 비밀번호는 `.env` 설정에 맞춰 작성하세요.

```sql
CREATE DATABASE <database_name>;
CREATE USER <database_user> WITH PASSWORD '<database_password>';
GRANT ALL PRIVILEGES ON DATABASE <database_name> TO <database_user>;
\q
```

### 6. 마이그레이션 실행

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. 관리자 계정 생성 선택 사항

```bash
python manage.py createsuperuser
```

### 8. Django 서버 실행

```bash
python manage.py runserver
```

서버 실행 후 기본 주소:

```text
http://localhost:8000
```

---

## 데이터베이스

Meal당은 PostgreSQL 기반으로 사용자, 식단, 혈당, 추천, 식당, 챗봇 데이터를 관리합니다.

주요 도메인은 다음과 같습니다.

- **accounts**  
  사용자 계정, OAuth 정보, 사용자 프로필, 임신 정보, 식이 제한, 목표 영양성분 관리

- **meals**  
  식단 기록, 음식 항목, 섭취량, 영양성분, YOLO 분석 결과 관리

- **blood_sugar**  
  혈당 실측값, 식후 혈당 예측값, 음식별 혈당 민감도 관리

- **recommend**  
  개인 맞춤형 식단 추천 결과 및 추천 근거 관리

- **location**  
  주변 식당 정보, 식당별 안전 점수, 방문 후 피드백 관리

- **chatbot**  
  FAQ, RAG 검색 근거, 사용자 질문, 챗봇 응답 로그 관리

ERD 또는 상세 테이블 구조는 프로젝트에 포함된 문서, ERD 링크, 또는 마이그레이션 파일을 확인하세요.

---

## 주요 API 도메인

실제 엔드포인트는 `urls.py`, API 문서 또는 Swagger 문서를 확인하세요.


```text
/api/auth/
/api/accounts/
/api/meals/
/api/blood-sugar/
/api/recommend/
/api/location/
/api/chatbot/
```

---

## 외부 라이브러리

주요 의존성은 `requirements.txt`를 확인하세요.

대표적으로 다음 라이브러리를 사용합니다.

- Django
- Django REST Framework
- djangorestframework-simplejwt
- PostgreSQL driver
- Celery
- RabbitMQ 연동 라이브러리
- httpx 또는 requests
- FastAPI 연동 관련 라이브러리
- YOLOv8 / ultralytics
- LightGBM
- ChromaDB
- sentence-transformers
- Gemini API 또는 LLM API 관련 라이브러리

백엔드 서버와 AI 서버가 분리되어 있는 경우 각 서버의 `requirements.txt`를 각각 확인하세요.

---

## 참고 / 문서

- Django 공식 문서  
  https://docs.djangoproject.com/

- Django REST Framework 공식 문서  
  https://www.django-rest-framework.org/

- PostgreSQL 공식 문서  
  https://www.postgresql.org/docs/

- Celery 공식 문서  
  https://docs.celeryq.dev/

- RabbitMQ 공식 문서  
  https://www.rabbitmq.com/documentation.html

- FastAPI 공식 문서  
  https://fastapi.tiangolo.com/

- Ultralytics YOLO 공식 문서  
  https://docs.ultralytics.com/

---

## 주의 사항

Meal당은 임신성 당뇨 산모의 식단 및 혈당 관리를 보조하기 위한 서비스입니다. 혈당 예측, 식단 추천, 챗봇 답변은 의료 진단이나 전문적인 치료를 대체하지 않습니다. 실제 치료, 약물 조절, 식단 변경은 반드시 전문 의료진의 안내를 따라야 합니다.
