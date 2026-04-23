from rest_framework import serializers

from doctors.models import Doctor
from patients.models import Patient

from .models import PatientDoctorMapping


class MappingInputSerializer(serializers.Serializer):
	patient_id = serializers.UUIDField()
	doctor_id = serializers.UUIDField()
	slot_start = serializers.DateTimeField(required=False, allow_null=True)
	slot_end = serializers.DateTimeField(required=False, allow_null=True)


class MappingFilterSerializer(serializers.Serializer):
	patient_id = serializers.UUIDField(required=False)


class PatientSummarySerializer(serializers.ModelSerializer):
	class Meta:
		model = Patient
		fields = ["id", "name", "age", "gender"]


class DoctorSummarySerializer(serializers.ModelSerializer):
	class Meta:
		model = Doctor
		fields = ["id", "name", "specialization", "hospital"]


class MappingOutputSerializer(serializers.ModelSerializer):
	patient = PatientSummarySerializer(read_only=True)
	doctor = DoctorSummarySerializer(read_only=True)

	class Meta:
		model = PatientDoctorMapping
		fields = ["id", "patient", "doctor", "slot_start", "slot_end", "assigned_at"]
