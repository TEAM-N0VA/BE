"""
Management command to load initial food data into FoodInfo table.

Usage:
    python manage.py load_food_data              # Load built-in sample data
    python manage.py load_food_data --api        # Fetch from 식약처 Open API
    python manage.py load_food_data --file path/to/foods.csv

CSV format:
    food_name,kcal_per_100,carbs_per_100,protein_per_100,fat_per_100,fiber_per_100,sugar_per_100,sodium_per_100,gi_index,serving_size
"""

import csv
import requests
from django.core.management.base import BaseCommand
from meals.models import FoodInfo


SAMPLE_FOODS = [
    # (food_name, kcal, carbs, protein, fat, fiber, sugar, sodium, gi_index, serving_size)
    ('현미밥', 156, 33.0, 3.5, 1.0, 1.8, 0.4, 2, 56, 150),
    ('잡곡밥', 150, 32.0, 3.8, 0.8, 2.0, 0.3, 55, 55, 150),
    ('흰쌀밥', 168, 37.0, 3.0, 0.3, 0.3, 0.1, 2, 72, 150),
    ('보리밥', 143, 30.0, 3.5, 0.9, 3.5, 0.3, 1, 50, 150),
    ('고구마', 128, 29.5, 1.5, 0.1, 2.9, 6.1, 20, 55, 100),
    ('감자', 77, 17.0, 2.0, 0.1, 1.5, 0.8, 5, 85, 100),
    ('닭가슴살', 165, 0.0, 31.0, 3.6, 0.0, 0.0, 74, 0, 100),
    ('삶은 달걀', 155, 1.1, 13.0, 10.6, 0.0, 1.1, 124, 0, 60),
    ('두부', 76, 1.9, 8.1, 4.2, 0.3, 0.5, 9, 15, 100),
    ('연어', 208, 0.0, 20.0, 13.4, 0.0, 0.0, 59, 0, 100),
    ('고등어', 183, 0.0, 18.1, 11.9, 0.0, 0.0, 89, 0, 100),
    ('브로콜리', 34, 5.3, 3.7, 0.4, 2.6, 1.7, 33, 15, 100),
    ('시금치', 23, 2.9, 2.9, 0.4, 2.2, 0.4, 79, 15, 100),
    ('양배추', 25, 5.8, 1.3, 0.1, 2.5, 3.2, 18, 15, 100),
    ('오이', 16, 3.1, 0.7, 0.1, 0.5, 2.2, 3, 15, 100),
    ('토마토', 18, 3.9, 0.9, 0.2, 1.2, 2.6, 5, 30, 100),
    ('사과', 52, 13.8, 0.3, 0.2, 2.4, 10.4, 1, 38, 100),
    ('바나나', 89, 22.8, 1.1, 0.3, 2.6, 12.2, 1, 51, 100),
    ('아몬드', 579, 21.6, 21.2, 49.9, 12.5, 4.4, 1, 15, 30),
    ('두유 (무가당)', 33, 1.5, 3.0, 1.5, 0.2, 0.7, 25, 34, 200),
    ('된장국', 30, 2.5, 2.8, 1.0, 0.8, 0.5, 500, 0, 200),
    ('미역국', 25, 2.0, 2.5, 0.8, 1.5, 0.3, 450, 0, 200),
    ('된장찌개', 65, 5.0, 5.0, 2.5, 1.5, 1.0, 800, 0, 250),
    ('삼계탕', 95, 3.5, 12.0, 3.5, 0.5, 0.5, 350, 0, 350),
    ('잡채', 183, 30.0, 4.5, 5.5, 2.0, 5.0, 450, 40, 200),
    ('비빔밥', 460, 72.0, 17.0, 11.0, 4.0, 5.0, 800, 55, 350),
    ('김치찌개', 90, 4.5, 7.5, 4.5, 1.5, 1.5, 1200, 0, 250),
    ('불고기', 185, 6.5, 17.5, 9.5, 0.5, 5.5, 600, 0, 150),
    ('닭가슴살 샐러드', 160, 8.0, 22.0, 4.5, 3.5, 4.0, 350, 0, 200),
    ('호박죽', 95, 18.0, 2.0, 0.5, 1.0, 5.0, 50, 65, 200),
    ('오트밀', 389, 66.3, 16.9, 6.9, 10.6, 0.0, 2, 55, 50),
    ('그릭요거트 (무가당)', 59, 3.6, 10.2, 0.4, 0.0, 3.6, 36, 11, 170),
    ('우유 (일반)', 61, 4.8, 3.2, 3.3, 0.0, 5.0, 44, 31, 200),
    ('통밀빵', 247, 48.0, 9.0, 3.4, 6.9, 5.6, 472, 51, 50),
    ('고구마 라떼 (시중)', 145, 30.0, 2.5, 2.0, 0.8, 18.0, 80, 62, 200),
]


class Command(BaseCommand):
    help = '식단 관리용 초기 음식 데이터를 FoodInfo 테이블에 로드합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api',
            action='store_true',
            help='식약처 Open API에서 데이터를 가져옵니다 (API 키 필요)',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='CSV 파일 경로에서 데이터를 로드합니다',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='로드 전에 기존 시스템 음식 데이터를 모두 삭제합니다',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = FoodInfo.objects.filter(is_user_added=False).delete()
            self.stdout.write(self.style.WARNING(f'기존 시스템 음식 {deleted}개 삭제됨'))

        if options['file']:
            self._load_from_csv(options['file'])
        elif options['api']:
            self._load_from_api()
        else:
            self._load_sample_data()

    def _load_sample_data(self):
        created = 0
        skipped = 0
        for row in SAMPLE_FOODS:
            (food_name, kcal, carbs, protein, fat,
             fiber, sugar, sodium, gi_index, serving_size) = row
            obj, is_new = FoodInfo.objects.get_or_create(
                food_name=food_name,
                is_user_added=False,
                defaults={
                    'kcal_per_100': kcal,
                    'carbs_per_100': carbs,
                    'protein_per_100': protein,
                    'fat_per_100': fat,
                    'fiber_per_100': fiber,
                    'sugar_per_100': sugar,
                    'sodium_per_100': sodium,
                    'gi_index': gi_index,
                    'serving_size': serving_size,
                }
            )
            if is_new:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'샘플 음식 데이터 로드 완료: {created}개 생성, {skipped}개 이미 존재'
        ))

    def _load_from_csv(self, filepath):
        created = 0
        errors = 0
        try:
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        FoodInfo.objects.get_or_create(
                            food_name=row['food_name'],
                            is_user_added=False,
                            defaults={
                                'kcal_per_100': float(row.get('kcal_per_100', 0)),
                                'carbs_per_100': float(row.get('carbs_per_100', 0)),
                                'protein_per_100': float(row.get('protein_per_100', 0)),
                                'fat_per_100': float(row.get('fat_per_100', 0)),
                                'fiber_per_100': float(row.get('fiber_per_100', 0)),
                                'sugar_per_100': float(row.get('sugar_per_100', 0)),
                                'sodium_per_100': float(row.get('sodium_per_100', 0)),
                                'gi_index': int(row['gi_index']) if row.get('gi_index') else None,
                                'serving_size': float(row.get('serving_size', 100)),
                            }
                        )
                        created += 1
                    except (KeyError, ValueError) as e:
                        self.stderr.write(f'행 처리 오류: {e} — {row}')
                        errors += 1
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {filepath}'))
            return

        self.stdout.write(self.style.SUCCESS(f'CSV 로드 완료: {created}개 처리, {errors}개 오류'))

    def _load_from_api(self):
        """식약처 식품영양성분 Open API 연동 (API 키 필요)"""
        from django.conf import settings
        api_key = getattr(settings, 'MFDS_API_KEY', '')
        if not api_key:
            self.stderr.write(self.style.ERROR(
                '식약처 API 키가 없습니다. .env에 MFDS_API_KEY를 설정하세요.'
            ))
            return

        # 식약처 API: https://www.foodsafetykorea.go.kr/api/openApiInfo.do
        url = 'http://openapi.foodsafetykorea.go.kr/api/{key}/I2790/json/1/1000'.format(key=api_key)
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'API 호출 실패: {e}'))
            return

        rows = data.get('I2790', {}).get('row', [])
        created = 0
        for row in rows:
            try:
                FoodInfo.objects.get_or_create(
                    food_name=row.get('FOOD_NM_KR', '').strip(),
                    is_user_added=False,
                    defaults={
                        'kcal_per_100': float(row.get('ENGY', 0) or 0),
                        'carbs_per_100': float(row.get('CARB', 0) or 0),
                        'protein_per_100': float(row.get('PROT', 0) or 0),
                        'fat_per_100': float(row.get('FAT', 0) or 0),
                        'fiber_per_100': float(row.get('FIBR', 0) or 0),
                        'sugar_per_100': float(row.get('SUGR', 0) or 0),
                        'sodium_per_100': float(row.get('NA', 0) or 0),
                        'serving_size': 100,
                    }
                )
                created += 1
            except (ValueError, KeyError):
                pass

        self.stdout.write(self.style.SUCCESS(f'식약처 API 로드 완료: {created}개 처리'))
