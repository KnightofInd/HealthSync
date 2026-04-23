import uuid

from django.conf import settings
from django.db import models


class Doctor(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="doctor_profile",
		db_index=True,
	)
	name = models.CharField(max_length=255)
	specialization = models.CharField(max_length=255)
	hospital = models.CharField(max_length=255, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return f"{self.name} ({self.specialization})"
