from django.urls import path

from .views import PatientDetailAPIView, PatientListCreateAPIView

urlpatterns = [
    path("", PatientListCreateAPIView.as_view(), name="patient-list-create"),
    path("<uuid:pk>/", PatientDetailAPIView.as_view(), name="patient-detail"),
]
