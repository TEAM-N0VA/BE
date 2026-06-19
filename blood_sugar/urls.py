from django.urls import path
from .views import (
    BloodSugarLogListCreateView,
    BloodSugarLogDetailView,
    BloodSugarPredictionView,
)

urlpatterns = [
    path('', BloodSugarLogListCreateView.as_view(), name='blood-sugar-list-create'),
    path('prediction', BloodSugarPredictionView.as_view(), name='blood-sugar-prediction'),
    path('<int:log_id>', BloodSugarLogDetailView.as_view(), name='blood-sugar-detail'),
]
