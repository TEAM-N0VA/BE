from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('accounts.urls_profile')),
    path('api/meals/', include('meals.urls')),
    path('api/blood-sugar/', include('blood_sugar.urls')),
    path('api/recommend/', include('recommend.urls')),
    path('api/location/', include('location.urls')),
    path('api/chatbot/', include('chatbot.urls')),
]
