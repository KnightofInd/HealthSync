from django.urls import path

from .views import MappingListCreateAPIView

urlpatterns = [
    path("", MappingListCreateAPIView.as_view(), name="patient-doctor-list-create"),
]
