import uuid

from django.db import models


class PatientDoctorMapping(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	patient = models.ForeignKey(
		"patients.Patient",
		on_delete=models.CASCADE,
		related_name="doctor_mappings",
		db_index=True,
	)
	doctor = models.ForeignKey(
		"doctors.Doctor",
		on_delete=models.CASCADE,
		related_name="patient_mappings",
		db_index=True,
	)
	slot_start = models.DateTimeField(null=True, blank=True, db_index=True)
	slot_end = models.DateTimeField(null=True, blank=True, db_index=True)
	assigned_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-assigned_at"]
		constraints = [
			models.UniqueConstraint(
				fields=["patient", "doctor"],
				name="unique_patient_doctor_mapping",
			)
		]

	def __str__(self):
		return f"{self.patient_id} -> {self.doctor_id}"
