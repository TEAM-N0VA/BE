# BE

# 밀당 백엔드 (BE)

## 로컬 개발 환경 세팅

### 1. 레포 클론
```bash
git clone https://github.com/TEAM-N0VA/BE.git
cd BE
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac
source .venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. .env 파일 생성
`.env` 파일 생성 후 값 채워넣기
(비밀번호 등 실제 값은 팀 노션 또는 카톡 참고)

### 5. PostgreSQL 설치 및 DB 생성
- PostgreSQL 설치 후 pgAdmin 실행
- pgAdmin에서 서버 연결 후 `mealdang_db` 데이터베이스 생성

### 6. 마이그레이션
```bash
python manage.py migrate
```

### 7. 서버 실행
```bash
python manage.py runserver
```

## 브랜치 전략
- `main` : 배포용
- `develop` : 개발 통합
- `feature/기능명` : 기능 개발
