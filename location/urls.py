from django.urls import path
from .views import (
    RestaurantListView,
    RestaurantDetailView,
    RestaurantFeedbackView,
)

urlpatterns = [
    path('restaurants', RestaurantListView.as_view(), name='restaurant-list'),
    path('restaurants/<int:restaurant_id>', RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('restaurants/<int:restaurant_id>/feedback', RestaurantFeedbackView.as_view(), name='restaurant-feedback'),
]
