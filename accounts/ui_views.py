from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate
from django.http import Http404
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import TemplateView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenRefreshView

from doctors.models import Doctor
from doctors.services import create_doctor, delete_doctor, list_doctors, update_doctor
from mappings.models import PatientDoctorMapping
from mappings.services import assign_doctor_to_patient, list_mappings_for_user
from patients.models import Patient
from patients.services import create_patient, delete_patient, list_patients_for_user, update_patient

from .models import User

ROLE_HOME_ROUTE = {
    User.RoleChoices.ADMIN: "ui-dashboard",
    User.RoleChoices.STAFF: "ui-patients",
    User.RoleChoices.DOCTOR: "ui-doctors",
    User.RoleChoices.OPS: "ui-mappings",
}


def get_role_home_route(role: str) -> str:
    return ROLE_HOME_ROUTE.get(role, "ui-dashboard")


def get_authenticated_ui_user(request):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
        return None

    try:
        token = AccessToken(access_token)
        user_id = token.get("user_id")
        if not user_id:
            return None
        return User.objects.filter(id=user_id, is_active=True).first()
    except Exception:
        return None


def get_or_create_doctor_profile_for_user(user):
    if user.role != User.RoleChoices.DOCTOR:
        return None

    doctor_profile = Doctor.objects.filter(user=user).first()
    if doctor_profile:
        return doctor_profile

    return Doctor.objects.create(
        user=user,
        name=user.name,
        specialization="General Medicine",
        hospital="Unassigned",
    )


def sync_doctor_profiles_from_users():
    doctor_users = User.objects.filter(role=User.RoleChoices.DOCTOR, is_active=True)
    for doctor_user in doctor_users:
        Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={
                "name": doctor_user.name,
                "specialization": "General Medicine",
                "hospital": "Unassigned",
            },
        )


class UILoginView(TemplateView):
    template_name = "ui/login.html"

    def get(self, request, *args, **kwargs):
        user = get_authenticated_ui_user(request)
        if user:
            return redirect(get_role_home_route(user.role))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, email=email, password=password)
        if not user:
            context = self.get_context_data(error="Invalid email or password.")
            return self.render_to_response(context, status=401)

        serializer = TokenObtainPairSerializer(data={"email": email, "password": password})
        serializer.is_valid(raise_exception=True)

        response = redirect(get_role_home_route(user.role))
        access_ttl = int(timedelta(minutes=30).total_seconds())
        refresh_ttl = int(timedelta(days=7).total_seconds())

        response.set_cookie(
            "access_token",
            serializer.validated_data["access"],
            max_age=access_ttl,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )
        response.set_cookie(
            "refresh_token",
            serializer.validated_data["refresh"],
            max_age=refresh_ttl,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )
        return response


class UIRefreshTokenView(TokenRefreshView):
    """Optional endpoint for client-driven token refresh workflows."""


class UIProtectedTemplateView(TemplateView):
    allowed_roles = set()

    def dispatch(self, request, *args, **kwargs):
        user = get_authenticated_ui_user(request)
        if not user:
            return redirect("ui-login")

        if self.allowed_roles and user.role not in self.allowed_roles:
            return redirect(get_role_home_route(user.role))

        request.ui_user = user
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ui_user"] = getattr(self.request, "ui_user", None)
        return context


class DashboardView(UIProtectedTemplateView):
    template_name = "ui/dashboard.html"
    allowed_roles = {User.RoleChoices.ADMIN}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recent_mappings = (
            PatientDoctorMapping.objects.select_related("patient", "doctor")
            .order_by("-assigned_at")[:8]
        )
        context.update(
            {
                "total_patients": Patient.objects.count(),
                "total_doctors": Doctor.objects.count(),
                "total_mappings": PatientDoctorMapping.objects.count(),
                "recent_mappings": recent_mappings,
            }
        )
        return context


class PatientsView(UIProtectedTemplateView):
    template_name = "ui/patients.html"
    allowed_roles = {User.RoleChoices.ADMIN, User.RoleChoices.STAFF}

    def _build_redirect_url(self, *, status: str, message: str, open_modal: bool = False, modal: str = ""):
        query = {
            "status": status,
            "message": message,
        }
        if open_modal:
            query["open_modal"] = "1"
        if modal:
            query["modal"] = modal
        return f"{reverse('ui-patients')}?{urlencode(query)}"

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip().lower()
        user = request.ui_user

        if action not in {"create", "update", "delete"}:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Unsupported action requested.",
                )
            )

        if action == "delete":
            patient_id = (request.POST.get("patient_id") or "").strip()
            patient = list_patients_for_user(user=user).filter(pk=patient_id).first()
            if not patient:
                return redirect(
                    self._build_redirect_url(
                        status="error",
                        message="Patient not found or access denied.",
                    )
                )
            delete_patient(patient=patient)
            return redirect(
                self._build_redirect_url(
                    status="success",
                    message="Patient removed successfully.",
                )
            )

        name = (request.POST.get("name") or "").strip()
        gender = (request.POST.get("gender") or "").strip().lower()
        age_raw = (request.POST.get("age") or "").strip()

        valid_genders = {Patient.GenderChoices.MALE, Patient.GenderChoices.FEMALE, Patient.GenderChoices.OTHER}
        if not name:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Patient name is required.",
                    open_modal=True,
                    modal="create" if action == "create" else "edit",
                )
            )

        try:
            age = int(age_raw)
            if age <= 0:
                raise ValueError
        except ValueError:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Age must be a positive number.",
                    open_modal=True,
                    modal="create" if action == "create" else "edit",
                )
            )

        if gender not in valid_genders:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Please choose a valid gender.",
                    open_modal=True,
                    modal="create" if action == "create" else "edit",
                )
            )

        if action == "create":
            create_patient(user=user, data={"name": name, "age": age, "gender": gender})
            return redirect(
                self._build_redirect_url(
                    status="success",
                    message="Patient added successfully.",
                )
            )

        patient_id = (request.POST.get("patient_id") or "").strip()
        patient = list_patients_for_user(user=user).filter(pk=patient_id).first()
        if not patient:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Patient not found or access denied.",
                )
            )

        update_patient(patient=patient, data={"name": name, "age": age, "gender": gender})
        return redirect(
            self._build_redirect_url(
                status="success",
                message="Patient updated successfully.",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.ui_user
        all_patients = list_patients_for_user(user=user).order_by("-created_at")
        patients = all_patients

        query_text = (self.request.GET.get("q") or "").strip()
        if query_text:
            patients = patients.filter(name__icontains=query_text)

        gender = (self.request.GET.get("gender") or "").strip().lower()
        valid_genders = {Patient.GenderChoices.MALE, Patient.GenderChoices.FEMALE, Patient.GenderChoices.OTHER}
        if gender in valid_genders:
            patients = patients.filter(gender=gender)

        selected_patient = None
        selected_patient_id = (self.request.GET.get("patient_id") or "").strip()
        if selected_patient_id:
            selected_patient = all_patients.filter(pk=selected_patient_id).first()

        context.update(
            {
                "patients": patients,
                "selected_patient": selected_patient,
                "total_patients": all_patients.count(),
                "active_filters": {
                    "q": query_text,
                    "gender": gender,
                },
                "ui_status": self.request.GET.get("status", ""),
                "ui_message": self.request.GET.get("message", ""),
                "ui_open_modal": self.request.GET.get("open_modal") == "1",
                "ui_modal_mode": self.request.GET.get("modal", "create"),
            }
        )
        return context


class DoctorsView(UIProtectedTemplateView):
    template_name = "ui/doctors.html"
    allowed_roles = {User.RoleChoices.ADMIN, User.RoleChoices.DOCTOR}

    def _build_redirect_url(self, *, status: str, message: str, open_modal: bool = False, modal: str = ""):
        query = {
            "status": status,
            "message": message,
        }
        if open_modal:
            query["open_modal"] = "1"
        if modal:
            query["modal"] = modal
        return f"{reverse('ui-doctors')}?{urlencode(query)}"

    def post(self, request, *args, **kwargs):
        if request.ui_user.role != User.RoleChoices.ADMIN:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Only admins can manage doctors.",
                )
            )

        action = (request.POST.get("action") or "").strip().lower()
        if action not in {"create", "update", "delete"}:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Unsupported action requested.",
                )
            )

        if action == "delete":
            doctor_id = (request.POST.get("doctor_id") or "").strip()
            doctor = list_doctors().filter(pk=doctor_id).first()
            if not doctor:
                return redirect(
                    self._build_redirect_url(
                        status="error",
                        message="Doctor not found.",
                    )
                )
            delete_doctor(doctor=doctor)
            return redirect(
                self._build_redirect_url(
                    status="success",
                    message="Doctor removed successfully.",
                )
            )

        name = (request.POST.get("name") or "").strip()
        specialization = (request.POST.get("specialization") or "").strip()
        hospital = (request.POST.get("hospital") or "").strip()

        if not name or not specialization:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Name and specialization are required.",
                    open_modal=True,
                    modal="create" if action == "create" else "edit",
                )
            )

        payload = {
            "name": name,
            "specialization": specialization,
            "hospital": hospital or None,
        }

        if action == "create":
            create_doctor(data=payload)
            return redirect(
                self._build_redirect_url(
                    status="success",
                    message="Doctor added successfully.",
                )
            )

        doctor_id = (request.POST.get("doctor_id") or "").strip()
        doctor = list_doctors().filter(pk=doctor_id).first()
        if not doctor:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Doctor not found.",
                )
            )

        update_doctor(doctor=doctor, data=payload)
        return redirect(
            self._build_redirect_url(
                status="success",
                message="Doctor updated successfully.",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.ui_user
        sync_doctor_profiles_from_users()

        doctor_profile = None
        assigned_mappings = PatientDoctorMapping.objects.none()

        if user.role == User.RoleChoices.DOCTOR:
            doctor_profile = get_or_create_doctor_profile_for_user(user)
            assigned_mappings = (
                PatientDoctorMapping.objects.filter(doctor=doctor_profile)
                .select_related("patient")
                .order_by("slot_start", "-assigned_at")
            )

        next_slot = None
        if user.role == User.RoleChoices.DOCTOR:
            next_slot = (
                assigned_mappings.filter(slot_start__isnull=False, slot_start__gte=timezone.now())
                .order_by("slot_start")
                .first()
            )

        all_doctors = list_doctors().order_by("name")
        doctors = all_doctors

        query_text = (self.request.GET.get("q") or "").strip()
        if query_text:
            doctors = doctors.filter(name__icontains=query_text)

        specialization = (self.request.GET.get("specialization") or "").strip()
        if specialization:
            doctors = doctors.filter(specialization__icontains=specialization)

        selected_doctor = None
        selected_doctor_id = (self.request.GET.get("doctor_id") or "").strip()
        if selected_doctor_id:
            selected_doctor = all_doctors.filter(pk=selected_doctor_id).first()

        context.update(
            {
                "doctor_profile": doctor_profile,
                "assigned_mappings": assigned_mappings,
                "assigned_patients_count": assigned_mappings.values("patient_id").distinct().count(),
                "scheduled_slots_count": assigned_mappings.filter(slot_start__isnull=False).count(),
                "next_slot": next_slot,
                "all_doctors": doctors,
                "selected_doctor": selected_doctor,
                "total_doctors": all_doctors.count(),
                "active_filters": {
                    "q": query_text,
                    "specialization": specialization,
                },
                "ui_status": self.request.GET.get("status", ""),
                "ui_message": self.request.GET.get("message", ""),
                "ui_open_modal": self.request.GET.get("open_modal") == "1",
                "ui_modal_mode": self.request.GET.get("modal", "create"),
            }
        )
        return context


class MappingsView(UIProtectedTemplateView):
    template_name = "ui/mappings.html"
    allowed_roles = {User.RoleChoices.ADMIN, User.RoleChoices.OPS}

    def _build_redirect_url(self, *, status: str, message: str, open_modal: bool = False):
        query = {
            "status": status,
            "message": message,
        }
        if open_modal:
            query["open_modal"] = "1"
        return f"/ui/mappings/?{urlencode(query)}"

    def post(self, request, *args, **kwargs):
        patient_id = request.POST.get("patient_id")
        doctor_id = request.POST.get("doctor_id")
        slot_start_raw = request.POST.get("slot_start") or None
        slot_end_raw = request.POST.get("slot_end") or None

        slot_start = parse_datetime(slot_start_raw) if slot_start_raw else None
        slot_end = parse_datetime(slot_end_raw) if slot_end_raw else None

        if slot_start and timezone.is_naive(slot_start):
            slot_start = timezone.make_aware(slot_start, timezone.get_current_timezone())

        if slot_end and timezone.is_naive(slot_end):
            slot_end = timezone.make_aware(slot_end, timezone.get_current_timezone())

        if not patient_id or not doctor_id:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Please select both a patient and a doctor.",
                    open_modal=True,
                )
            )

        if slot_start and slot_end and slot_end <= slot_start:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Slot end time must be after start time.",
                    open_modal=True,
                )
            )

        try:
            assign_doctor_to_patient(
                user=request.ui_user,
                patient_id=patient_id,
                doctor_id=doctor_id,
                slot_start=slot_start,
                slot_end=slot_end,
            )
        except ValidationError as exc:
            detail = getattr(exc, "detail", "Unable to create mapping.")
            if isinstance(detail, dict):
                detail = detail.get("detail", detail)
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message=str(detail),
                    open_modal=True,
                )
            )
        except PermissionDenied as exc:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message=str(exc),
                    open_modal=True,
                )
            )
        except Http404:
            return redirect(
                self._build_redirect_url(
                    status="error",
                    message="Selected patient or doctor was not found.",
                    open_modal=True,
                )
            )

        return redirect(
            self._build_redirect_url(
                status="success",
                message="Doctor assigned successfully.",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sync_doctor_profiles_from_users()

        user = self.request.ui_user
        mappings = list_mappings_for_user(user=user)

        patients = Patient.objects.all().order_by("name")
        doctors = Doctor.objects.all().order_by("name")

        context.update(
            {
                "mappings": mappings,
                "patients": patients,
                "doctors": doctors,
                "total_mappings": mappings.count(),
                "unassigned_patients": patients.filter(doctor_mappings__isnull=True).count(),
                "ui_status": self.request.GET.get("status", ""),
                "ui_message": self.request.GET.get("message", ""),
                "ui_open_modal": self.request.GET.get("open_modal") == "1",
            }
        )
        return context


class UILogoutView(View):
    def get(self, request, *args, **kwargs):
        response = redirect("ui-login")
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
