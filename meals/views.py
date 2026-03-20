from django.http import JsonResponse

def test_connection(request):
    return JsonResponse(
        {"message": "서버 연결 성공"},
        json_dumps_params={'ensure_ascii': False} # 한글 깨짐 방지
    )