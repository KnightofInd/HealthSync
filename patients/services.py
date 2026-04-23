from django.shortcuts import get_object_or_404

from accounts.models import User

from .models import Patient


def list_patients_for_user(*, user):
	queryset = Patient.objects.all()
	if user.role != User.RoleChoices.ADMIN:
		queryset = queryset.filter(created_by=user)

	return (
		queryset
		.select_related("created_by")
		.prefetch_related("doctor_mappings__doctor")
	)


def create_patient(*, user, data):
	return Patient.objects.create(created_by=user, **data)


def get_patient_by_id(*, patient_id):
	return get_object_or_404(
		Patient.objects.select_related("created_by").prefetch_related(
			"doctor_mappings__doctor"
		),
		pk=patient_id,
	)


def update_patient(*, patient, data):
	for key, value in data.items():
		setattr(patient, key, value)
	patient.save()
	return patient


def delete_patient(*, patient):
	patient.delete()
