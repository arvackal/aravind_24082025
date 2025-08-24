from django.urls import path
from .views import GetReportAPIView, TriggerReportAPI
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('triggerreport/',TriggerReportAPI.as_view(), name = 'triggerreportapi'),
    path('getreport/<str:report_id>/',GetReportAPIView.as_view(), name = 'getreportapi')
]

