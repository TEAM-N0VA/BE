from django.urls import path
from .views import (
    ProfileView, DashboardTodayView,
    ReportCalendarView, ReportDailyView,
)

urlpatterns = [
    path('profile', ProfileView.as_view(), name='profile'),
    path('dashboard/today', DashboardTodayView.as_view(), name='dashboard-today'),
    path('report/calendar', ReportCalendarView.as_view(), name='report-calendar'),
    path('report/daily', ReportDailyView.as_view(), name='report-daily'),
]
