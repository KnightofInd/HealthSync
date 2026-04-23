from rest_framework import serializers

from .models import User


class RegisterInputSerializer(serializers.Serializer):
	name = serializers.CharField(max_length=255)
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True, min_length=8)

	def validate_email(self, value):
		if User.objects.filter(email__iexact=value).exists():
			raise serializers.ValidationError("A user with this email already exists.")
		return value


class UserOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ["id", "name", "email", "role", "created_at"]
