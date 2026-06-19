from django.urls import path
from .views import (
    RecommendStatusView,
    RecommendRequestView,
    RecommendHistoryView,
    RecommendFeedbackView,
)

urlpatterns = [
    path('status', RecommendStatusView.as_view(), name='recommend-status'),
    path('request', RecommendRequestView.as_view(), name='recommend-request'),
    path('history', RecommendHistoryView.as_view(), name='recommend-history'),
    path('<int:recommend_id>/feedback', RecommendFeedbackView.as_view(), name='recommend-feedback'),
]
