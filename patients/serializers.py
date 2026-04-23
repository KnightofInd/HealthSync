from rest_framework import serializers

from .models import Patient


class PatientInputSerializer(serializers.ModelSerializer):
	class Meta:
		model = Patient
		fields = ["name", "age", "gender"]

	def validate_age(self, value):
		if value <= 0:
			raise serializers.ValidationError("Age must be greater than 0.")
		return value


class PatientOutputSerializer(serializers.ModelSerializer):
	created_by = serializers.UUIDField(source="created_by_id", read_only=True)

	class Meta:
		model = Patient
		fields = [
			"id",
			"name",
			"age",
			"gender",
			"created_by",
			"created_at",
			"updated_at",
		]
