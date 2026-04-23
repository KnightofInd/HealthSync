from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User
from doctors.models import Doctor
from patients.models import Patient

from .models import PatientDoctorMapping


def list_mappings_for_user(*, user, patient_id=None):
	queryset = PatientDoctorMapping.objects.select_related("patient", "doctor")
	if user.role == User.RoleChoices.STAFF:
		queryset = queryset.filter(patient__created_by=user)

	if patient_id is not None:
		patient = get_object_or_404(Patient, pk=patient_id)
		if user.role == User.RoleChoices.STAFF and patient.created_by_id != user.id:
			raise PermissionDenied("You do not have access to this patient.")
		queryset = queryset.filter(patient_id=patient_id)

	return queryset


def assign_doctor_to_patient(*, user, patient_id, doctor_id, slot_start=None, slot_end=None):
	patient = get_object_or_404(Patient, pk=patient_id)
	if user.role == User.RoleChoices.STAFF and patient.created_by_id != user.id:
		raise PermissionDenied("You do not have access to this patient.")

	doctor = get_object_or_404(Doctor, pk=doctor_id)

	mapping, created = PatientDoctorMapping.objects.get_or_create(
		patient=patient,
		doctor=doctor,
		defaults={
			"slot_start": slot_start,
			"slot_end": slot_end,
		},
	)
	if not created:
		raise ValidationError({"detail": "Doctor is already assigned to this patient."})

	return mapping
