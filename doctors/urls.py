from django.urls import path

from .views import DoctorDetailAPIView, DoctorListCreateAPIView

urlpatterns = [
    path("", DoctorListCreateAPIView.as_view(), name="doctor-list-create"),
    path("<uuid:pk>/", DoctorDetailAPIView.as_view(), name="doctor-detail"),
]
