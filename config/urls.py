"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import include, path

from accounts.ui_views import (
    DashboardView,
    DoctorsView,
    MappingsView,
    PatientsView,
    UILoginView,
    UILogoutView,
)

urlpatterns = [
    path("", UILoginView.as_view(), name="ui-login"),
    path("ui/login/", UILoginView.as_view(), name="ui-login-post"),
    path("ui/logout/", UILogoutView.as_view(), name="ui-logout"),
    path("ui/dashboard/", DashboardView.as_view(), name="ui-dashboard"),
    path("ui/patients/", PatientsView.as_view(), name="ui-patients"),
    path("ui/doctors/", DoctorsView.as_view(), name="ui-doctors"),
    path("ui/mappings/", MappingsView.as_view(), name="ui-mappings"),
    path("api/auth/", include("accounts.urls")),
    path("api/patients/", include("patients.urls")),
    path("api/doctors/", include("doctors.urls")),
    path("api/patient-doctors/", include("mappings.urls")),
]
