from django.urls import path
from .views import (
    UploadUrlView, AnalyzeImageView,
    FoodSearchView, FoodDetailView, FoodCreateView,
    MealLogListCreateView, MealLogDetailView,
)

urlpatterns = [
    path('upload-url', UploadUrlView.as_view(), name='meal-upload-url'),
    path('analyze-image', AnalyzeImageView.as_view(), name='meal-analyze-image'),
    path('search', FoodSearchView.as_view(), name='food-search'),
    path('foods/<int:food_id>', FoodDetailView.as_view(), name='food-detail'),
    path('foods', FoodCreateView.as_view(), name='food-create'),
    path('', MealLogListCreateView.as_view(), name='meal-log-list-create'),
    path('<int:meal_id>', MealLogDetailView.as_view(), name='meal-log-detail'),
]
