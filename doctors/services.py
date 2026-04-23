from django.shortcuts import get_object_or_404

from .models import Doctor


def list_doctors():
	return Doctor.objects.prefetch_related("patient_mappings__patient")


def create_doctor(*, data):
	return Doctor.objects.create(**data)


def get_doctor_by_id(*, doctor_id):
	return get_object_or_404(
		Doctor.objects.prefetch_related("patient_mappings__patient"),
		pk=doctor_id,
	)


def update_doctor(*, doctor, data):
	for key, value in data.items():
		setattr(doctor, key, value)
	doctor.save()
	return doctor


def delete_doctor(*, doctor):
	doctor.delete()
