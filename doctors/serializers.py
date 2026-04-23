from rest_framework import serializers

from .models import Doctor


class DoctorInputSerializer(serializers.ModelSerializer):
	class Meta:
		model = Doctor
		fields = ["name", "specialization", "hospital"]


class DoctorOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = Doctor
		fields = ["id", "name", "specialization", "hospital", "created_at"]
