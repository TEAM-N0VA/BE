#!/bin/bash
# 밀당 백엔드 로컬 개발 환경 셋업 스크립트
set -e

echo "========================================="
echo "  밀당 (Meal당) 백엔드 셋업 시작"
echo "========================================="

# 1. 가상환경 생성 및 활성화
if [ ! -d ".venv" ]; then
    echo "[1/6] 가상환경 생성 중..."
    python3 -m venv .venv
fi

echo "[1/6] 가상환경 활성화..."
source .venv/bin/activate

# 2. 패키지 설치
echo "[2/6] 패키지 설치 중..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "      패키지 설치 완료"

# 3. .env 파일 확인
if [ ! -f ".env" ]; then
    echo "[3/6] .env 파일이 없습니다. .env.example에서 복사합니다..."
    cp .env.example .env
    echo "      .env 파일을 열어 실제 값을 입력하세요."
else
    echo "[3/6] .env 파일 확인 완료"
fi

# 4. DB 마이그레이션
echo "[4/6] DB 마이그레이션 실행 중..."
python manage.py migrate
echo "      마이그레이션 완료"

# 5. 초기 음식 데이터 로딩
echo "[5/6] 초기 음식 데이터 로딩 중..."
python manage.py load_food_data
echo "      음식 데이터 로딩 완료"

# 6. 슈퍼유저 생성 (선택)
echo "[6/6] 관리자 계정 생성 (선택사항)"
read -p "      관리자 계정을 만드시겠습니까? (y/N): " CREATE_SUPER
if [[ "$CREATE_SUPER" == "y" || "$CREATE_SUPER" == "Y" ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "========================================="
echo "  셋업 완료!"
echo ""
echo "  서버 실행:    source .venv/bin/activate && python manage.py runserver"
echo "  Celery 실행:  source .venv/bin/activate && celery -A config worker -l info"
echo "  관리자 페이지: http://localhost:8000/admin/"
echo "  API 베이스:   http://localhost:8000/api/"
echo "========================================="
