import uuid

from django.conf import settings
from django.db import models


class Patient(models.Model):
	class GenderChoices(models.TextChoices):
		MALE = "male", "Male"
		FEMALE = "female", "Female"
		OTHER = "other", "Other"

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=255)
	age = models.PositiveIntegerField()
	gender = models.CharField(max_length=16, choices=GenderChoices.choices)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="patients",
		db_index=True,
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return self.name
